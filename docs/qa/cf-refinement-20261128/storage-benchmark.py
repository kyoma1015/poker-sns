import json,subprocess,io,hashlib,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from gto.qualification import public_stream_study as old,refine_checkpoint as cp
from gto.qualification.policy import sha

def meta(path):
 p=path/'identity.json.zst';r=json.load(open(path/'receipt.json'));assert sha(p)==r['identity_sha256'];return json.loads(subprocess.check_output(['zstd','-q','-d','-c',str(p)]))
def stub(m):
 sets=[[old.freeze(k) for k in row] for row in m['layout']['keysets']];keys=[None if i<0 else sets[i] for i in m['layout']['node_keyset']];base=[];S=0
 for k,n in enumerate(m['nodes']):base.append(S);S+=0 if n['actor']<0 else len(keys[k])*len(n['children'])
 return SimpleNamespace(keys=keys,base=base,S=S,nodes=m['nodes'],R=np.zeros(S),A=np.zeros(S),prior=np.zeros(S),visits=np.zeros(S,dtype=np.uint16))
rows=[]
for seed in (17120101,17120102):
 parentpath=Path(f'docs/qa/public-stream-final-20261127/{seed}/t64');pm=meta(parentpath);parent=stub(pm)
 for e in pm['arrays']:
  p=parentpath/e['path'];assert sha(p)==e['sha256'];a=np.load(io.BytesIO(subprocess.check_output(['zstd','-q','-d','-c',str(p)])),allow_pickle=False);getattr(parent,e['field'])[e['offset']:e['offset']+len(a)]=a
 path=Path(f'docs/qa/cf-refinement-20261128/{seed}/refined/last');m=meta(path);q=stub(m);cp.decode(q,parent,path,m);full=0;tick=time.process_time()
 for field in ('R','A','prior','visits'):
  a=getattr(q,field).view(np.uint8)
  for i in range(0,len(a),4000000):
   raw=a[i:i+4000000].tobytes();b=subprocess.check_output(['zstd','-q','-1','-c'],input=raw);assert subprocess.check_output(['zstd','-q','-d','-c'],input=b)==raw;full+=len(b)
 delta=m['compressed_array_bytes'];r=dict(seed=seed,logical_array_bytes=m['logical_array_bytes'],full_zstd_array_bytes=full,aligned_XOR_zstd_array_bytes=delta,saving_fraction=1-delta/full,exact_SHA_and_full_chunk_roundtrip=True,scope='same reconstructed arrays, same4MB chunks/level1; metadata/immutable-parent cost excluded; historical1.63GB untouched');rows.append(r);print(r,flush=True)
Path('docs/qa/cf-refinement-20261128/storage-benchmark.json').write_text(json.dumps(dict(rows=rows),indent=2)+'\n')
