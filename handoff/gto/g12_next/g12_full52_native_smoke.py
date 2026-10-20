import json,time,hashlib,tempfile,pathlib
from fractions import Fraction
from pokerid_rules import Rules
import pokerid_g11,pokerid_g12
class Full52Native:
 _g11_native_spec=True
 def __init__(self):
  self.stacks=[300*80]*9
  self.rules=Rules(bb=80,bba=80,ante_order='ante_first',stack_basis='before_ante',dead_eligibility='all_live',rake_rate=Fraction(1,10),rake_cap=None,no_flop_no_drop=True,cap_scope='whole_hand',rounding='floor',rake_ante=True)
  d=self.rules.manifest();d.pop('version');d['rate_num']=1;d['rate_den']=10
  self._native_rules=d;self.root_actions=[];self.fixture=None
  self._public_config_json=json.dumps({'schema':1,'game_format':'cash','stacks':self.stacks,'rules':self.rules.manifest(),'fixture':None},sort_keys=True,separators=(',',':'))
 def num_players(self):return 9

g=Full52Native();result={}
for label,mod in [('G11_wide',pokerid_g11),('G12_wide',pokerid_g12)]:
 s=mod.Solver(g,.6,17,True,True,.1);t=time.process_time();err=None
 try:
  for i in range(100):s.run_iteration()
 except Exception as e:err=repr(e)
 result[label]={'iteration':s.iteration,'cpu_seconds':time.process_time()-t,'error':err,'infosets':s.stats()['infosets'],'legal_entries':s.stats()['legal_entries'],'rng_state_sha256':hashlib.sha256(s.rng_state().encode()).hexdigest()}
 if not err:
  with tempfile.TemporaryDirectory() as d:
   f=pathlib.Path(d)/'s';s.save_binary(str(f),'full52-native-smoke');result[label]['payload_sha256']=hashlib.sha256(f.read_bytes()[8:]).hexdigest()
pathlib.Path('logs_g12/full52_native_smoke.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
