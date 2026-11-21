"""Portable lossless frozen inputs; no training/remote data required."""
import base64,gzip,hashlib,json,struct
from pathlib import Path
from gto.abstract.study import digest

def pack(root):
 root=Path(root);e=json.loads((root/'evidence.json').read_text());k=json.load(gzip.open(root/f"kernel-{e['validation_seed']}.json.gz",'rt'));s=k['samples_per_class_pair'];raw=bytearray()
 for mean,var in zip(k['mean'],k['variance']):
  total=round(2*s*mean);squared=round(4*((s-1)*var+s*mean*mean));raw.extend(struct.pack('<iI',total,squared))
 policies={}
 for mode in ('checkdown','flop_controller'):
  p=json.loads((root/f"policy-{e['seeds'][0]}-{mode}.json").read_text());data=struct.pack('<'+'d'*len(p['strategy']),*p['strategy'])
  observed=next(r for r in e['runs'] if r['seed']==e['seeds'][0] and r['mode']==mode)
  policies[mode]={'bytes_sha256':hashlib.sha256(data).hexdigest(),'policy_digest':observed['policy_digest'],'training_payoff_digest':p['kernel_digest'],'data':base64.b64encode(gzip.compress(data,mtime=0)).decode()}
 return {'schema':'pokerid-fixed-ev-archive-v1','condition':e['condition'],'tree':p['tree'],'seed':k['seed'],'samples':s,
  'kernel_bytes_sha256':hashlib.sha256(raw).hexdigest(),'kernel_data':base64.b64encode(gzip.compress(raw,mtime=0)).decode(),
  'kernel_mean_digest':digest(k['mean']),'policies':policies,'full_game_gto_verified':False}

def unpack(packet):
 from gto.abstract.model import CONDITION,tree
 if packet.get('condition')!=CONDITION or packet.get('tree')!=tree() or type(packet.get('samples')) is not int or not 2<=packet['samples']<=100000:raise ValueError('frozen HU50 condition/tree/sample design differs')
 if packet['schema']!='pokerid-fixed-ev-archive-v1' or packet['full_game_gto_verified'] is not False:raise ValueError('research archive required')
 raw=gzip.decompress(base64.b64decode(packet['kernel_data'],validate=True));s=packet['samples'];mean=[];variance=[]
 if len(raw)!=5*169*169*8 or hashlib.sha256(raw).hexdigest()!=packet['kernel_bytes_sha256']:raise ValueError('kernel archive integrity differs')
 for total,squared in struct.iter_unpack('<iI',raw):
  if abs(total)>200*s or squared>40000*s or s*squared<total*total:raise ValueError('invalid exact integer payoff moments')
  m=(total/2)/s;v=max(0.,(squared/4-(total/2)*(total/2)/s)/(s-1));mean.append(m);variance.append(v)
 if digest(mean)!=packet['kernel_mean_digest']:raise ValueError('kernel mean identity differs')
 policies={}
 for mode,p in packet['policies'].items():
  data=gzip.decompress(base64.b64decode(p['data'],validate=True))
  if hashlib.sha256(data).hexdigest()!=p['bytes_sha256']:raise ValueError('policy bytes differ')
  values=list(struct.unpack('<'+'d'*(len(data)//8),data))
  if digest(values)!=p['policy_digest']:raise ValueError('policy identity differs')
  policies[mode]=values
 return {'seed':packet['seed'],'samples_per_class_pair':s,'mean':mean,'variance':variance},policies

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=pack(a.archive);unpack(r);a.output.write_text(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n');print('PASS lossless frozen archive')
