"""Lossless aligned XOR checkpoint deltas; immutable parent bytes never removed.
Saves only new evidence. Historical Git blobs/repository size is not reduced.
"""
import hashlib,json,subprocess,io,random
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from gto.qualification import public_stream_study as old,stream_sampling as ss,active_chance as ac,stream_features
from gto.qualification.policy import sha

def aligned(q,parent,field):
    out=np.zeros(q.S,dtype=getattr(q,field).dtype)
    if len(q.nodes)!=len(parent.nodes):raise ValueError('same public tree delta only')
    for k,n in enumerate(q.nodes):
        if n['actor']<0:continue
        count=len(n['children']);length=len(parent.keys[k])*count
        if q.keys[k][:len(parent.keys[k])]!=parent.keys[k]:raise ValueError('parent key prefix identity')
        out[q.base[k]:q.base[k]+length]=getattr(parent,field)[parent.base[k]:parent.base[k]+length]
    return out

def encode(q,parent,folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False);records=[];logical=0
    for field in ('R','A','prior','visits'):
        array=getattr(q,field);base=aligned(q,parent,field);delta=np.bitwise_xor(array.view(np.uint8),base.view(np.uint8));logical+=array.nbytes;parts=[]
        for i in range(0,len(delta),4000000):
            p=folder/f'{field}-{i}.xor.zst'
            with p.open('wb') as out:subprocess.run(['zstd','-q','-1','-c'],input=delta[i:i+4000000].tobytes(),stdout=out,check=True)
            parts.append(dict(path=p.name,offset=i,sha256=sha(p)))
        records.append(dict(field=field,dtype=array.dtype.str,sha256=hashlib.sha256(array.tobytes()).hexdigest(),parts=parts))
    return dict(records=records,logical_array_bytes=logical,compressed_array_bytes=sum(p.stat().st_size for p in folder.glob('*.zst')))

def decode(q,parent,folder,meta):
    folder=Path(folder)
    for record in meta['records']:
        field=record['field'];out=aligned(q,parent,field)
        if out.dtype.str!=record['dtype']:raise ValueError('delta dtype')
        data=out.view(np.uint8)
        for part in record['parts']:
            p=folder/part['path']
            if sha(p)!=part['sha256']:raise ValueError('delta shard SHA')
            raw=np.frombuffer(subprocess.check_output(['zstd','-q','-d','-c',str(p)]),dtype=np.uint8);i=part['offset'];data[i:i+len(raw)]^=raw
        if hashlib.sha256(out.tobytes()).hexdigest()!=record['sha256']:raise ValueError('reconstructed array SHA')
        setattr(q,field,out)

def save(q,parent,folder,identity,rng):
    folder=Path(folder);delta=encode(q,parent,folder)
    meta=dict(identity,**delta,S=q.S,t=q.t,blocks=[{k:b[k] for k in ('board','weight','stratum')} for b in q.blocks],layout=old.layout(q),rng=old.plain(rng.getstate()))
    p=folder/'identity.json.zst'
    with p.open('wb') as out:subprocess.run(['zstd','-q','-1','-c'],input=json.dumps(meta,sort_keys=True,separators=(',',':')).encode(),stdout=out,check=True)
    (folder/'receipt.json').write_text(json.dumps(dict(identity_sha256=sha(p),t=q.t,S=q.S,**{k:delta[k] for k in ('logical_array_bytes','compressed_array_bytes')}),indent=2)+'\n')

def restore(folder,parent):
    folder=Path(folder);receipt=json.loads((folder/'receipt.json').read_text());p=folder/'identity.json.zst'
    if sha(p)!=receipt['identity_sha256']:raise ValueError('delta identity SHA')
    meta=json.loads(subprocess.check_output(['zstd','-q','-d','-c',str(p)]))
    for path,h in meta['sources'].items():
        if sha(Path(path))!=h:raise ValueError('refinement source SHA '+path)
    if sha(Path(parent.lib._name))!=meta['binary_sha256']:raise ValueError('refinement build SHA')
    keys=[[old.freeze(k) for k in row] for row in meta['layout']['keysets']];keys=[None if j<0 else keys[j] for j in meta['layout']['node_keyset']];base=[];S=0
    for k,n in enumerate(meta['nodes']):base.append(S);S+=0 if n['actor']<0 else len(keys[k])*len(n['children'])
    if S!=meta['S']:raise ValueError('delta layout')
    stub=SimpleNamespace(S=S,keys=keys,base=base,nodes=meta['nodes'],t=meta['t'],rows=[(base[k],len(keys[k]),len(n['children']),k) for k,n in enumerate(meta['nodes']) if n['actor']>=0],R=np.zeros(S),A=np.zeros(S),prior=np.zeros(S),visits=np.zeros(S,dtype=np.uint16))
    decode(stub,parent,folder,meta)
    from gto.qualification.public_chance_solver import block
    blocks=[dict(block(parent.lib,b['board'],b['weight']),stratum=b['stratum']) for b in meta['blocks']]
    q=ss.Game(parent.lib,meta['nodes'],blocks,meta['splits'],previous=stub);q.initial_average=np.zeros(q.S);q.initial_regret=np.zeros(q.S)
    if q.S!=S:raise ValueError('unexpected restored infosets')
    rng=random.Random();rng.setstate(old.freeze(meta['rng']));return q,meta,rng
