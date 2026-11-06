"""Portable replay of checksummed binary packets, with explicit numeric tolerance."""
import argparse,json,math
from pathlib import Path
from gto.abstract.fullsupport import unpack

def compare(a,b,path='root'):
 if type(a)!=type(b):raise ValueError('replay type '+path)
 if isinstance(a,dict):
  if a.get('codec')=='f64le-zlib-base64':
   if a['count']!=b['count']:raise ValueError('packet shape '+path)
   compare(unpack(a),unpack(b),path+'.decoded');return
  if set(a)!=set(b):raise ValueError('replay fields '+path)
  for k in a:compare(a[k],b[k],path+'.'+k)
 elif isinstance(a,list):
  if len(a)!=len(b):raise ValueError('replay shape '+path)
  for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+f'[{i}]')
 elif isinstance(a,float):
  if not math.isfinite(a) or not math.isclose(a,b,rel_tol=0,abs_tol=1e-12):raise ValueError('replay number '+path)
 elif a!=b:raise ValueError('replay identity '+path)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--actual',type=Path,required=True);p.add_argument('--expected',type=Path,required=True);v=p.parse_args();compare(json.loads(v.actual.read_text()),json.loads(v.expected.read_text()));print('PASS independent fixed-game numeric/source/policy replay; external GTO remains unverified')
