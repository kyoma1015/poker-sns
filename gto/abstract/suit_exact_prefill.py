"""Finite optional cache prefill; integration order/representatives remain unchanged."""
import argparse,json
from pathlib import Path
from gto.abstract import suit_exact as s,fullsupport as fs,independent_preflop as old,call_study as cs,root_interval as ri
from gto.abstract.factorial_transfer import category
from gto.abstract.range_study import sha

def prefill(root,cache,limit):
 d=json.loads(s.DESIGN.read_text())
 if d['source_sha256']!=s.sources():raise ValueError('exact source changed')
 env=cs.setup(root/'env');native=fs.build(root/'oracle');coeff=ri.build(root/'coeff');teacher=json.loads(old.TEACHER.read_text());p=json.loads(old.P.read_text());coefs={c:fs.coefficients(teacher,p,c,coeff) for c in sorted({x['category'] for x in json.loads(old.DESIGN.read_text())['teacher']})};identity={'teacher_sha256':sha(old.TEACHER),'source_sha256':old.sources(),'frozen_preflop_digest':env[4]};cache.mkdir(parents=True,exist_ok=True)
 for i,row in enumerate(reversed(d['orbits'][-limit:])):
  f=row['representative'];path=cache/(fs.digest({'identity':identity,'flop':f})+'.json')
  if path.exists():continue
  y,m=fs.evaluate_flop(native,env[0],f,coefs[category(f)]);temp=path.with_suffix('.prefill-tmp');temp.write_text(json.dumps({'identity':identity,'flop':f,'payoff':fs.pack(y),'mass':fs.pack(m)},sort_keys=True,separators=(',',':'))+'\n');temp.replace(path)
  if (i+1)%32==0:print(json.dumps({'prefill_reverse_complete':i+1,'maximum':limit}),flush=True)

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--build-dir',type=Path,required=True);a.add_argument('--cache-dir',type=Path,required=True);a.add_argument('--limit',type=int,default=1000);v=a.parse_args()
 if not 1<=v.limit<=1755:a.error('finite registered orbit prefix required')
 prefill(v.build_dir,v.cache_dir,v.limit)
