"""Compare the regenerated research artifact, including provenance and scope."""
import argparse,json,math
from pathlib import Path

def compare(a,b,path='root'):
 if type(a)!=type(b):raise ValueError('research type differs: '+path)
 if isinstance(a,dict):
  if set(a)!=set(b):raise ValueError('research fields differ: '+path)
  for k in a:compare(a[k],b[k],path+'.'+k)
 elif isinstance(a,list):
  if len(a)!=len(b):raise ValueError('research shape differs: '+path)
  for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+f'[{i}]')
 elif type(a) is float:
  if not math.isfinite(a) or not math.isclose(a,b,rel_tol=0,abs_tol=1e-12):raise ValueError('research number differs: '+path)
 elif a!=b:raise ValueError('research identity differs: '+path)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--actual',type=Path,required=True);p.add_argument('--expected',type=Path,required=True);a=p.parse_args()
 compare(json.loads(a.actual.read_text()),json.loads(a.expected.read_text()))
 print('PASS abstract research source/seed/policy/169frequency/EV regeneration; full-game GTO remains unverified')
