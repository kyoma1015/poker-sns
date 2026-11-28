import gzip,json
from pathlib import Path
from dataclasses import replace
from gto.qualification.build import load
from gto.qualification.multiplayer_joint import SparseJoint,observation,sparse_key
from gto.native.training import NativeGame
from gto.abstract import model
from gto.qualification.variance_study import compressed
_,native=load('/tmp/poker-public-response-build');root=Path('docs/qa/sparse-generalization-20261124/multiplayer-lazy')
for n in (6,9):
 game=NativeGame([100-20*(p%3) for p in range(n)],bba=2,rake_num=1,rake_den=20)
 for seed in (17124101,17124102):
  q=SparseJoint(native,game,seed=seed,average_mode='lazy');q.restore(json.loads(gzip.decompress((root/f'{n}max-{seed}-final.json.gz').read_bytes())));profile=q.profile();rows={}
  def state(prefix):
   s=native.NativeState(game)
   for c in range(2*n):s.apply_action(c)
   for a in prefix:s.apply_action(a)
   return s
  def export(name,s):
   o=observation(s);out={}
   for label,g in zip(model.CLASSES,model.classes()):
    actual=replace(o,own=tuple(g[0]));p=profile.response.provider(actual);key=sparse_key(actual)
    out[label]=dict(actor=o.actor,actions=list(o.actions),frequencies={str(k):v for k,v in p.items()},average_trained=bool(key in q.A and sum(q.A[key])>0),regret_trained=q.R_visits.get(key,0)>0,EV=None)
   rows[name]=out
  prefix=[]
  for _ in range(n-1):
   s=state(prefix);export('RFI-seat'+str(s.current_player()),s);prefix.append(0)
  prefix=[0]*(n-2)+[8];export('BB-vs-SB-open3',state(prefix));export('SB-vs-BB-3bet10',state(prefix+[22]))
  compressed(root/f'{n}max-{seed}-169-frequencies.json.gz',dict(policy_digest=q.policy_digest,contexts=rows,formal_pass=False,formal_verified_strategies=0,scope='research only; unseen rows explicit uniform legal scope, no EV qualification'))
