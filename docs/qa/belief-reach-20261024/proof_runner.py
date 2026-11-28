from fractions import Fraction as F
import importlib,os,sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()));sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR'])
from gto.native.history_reach import bounded_belief_value,immutable_average_policy
from gto.native.training import NativeGame
n=importlib.import_module('pokerid_g12');g=NativeGame([4,4])
def value(deals,history,policy,**kw):return bounded_belief_value(n,g,[0,5],deals,history,policy,**kw)
river=value([([48,49],F(1,4)),([40,45],F(3,4))],[1,1,1,8,17,1,1,26,1,1,35,1,1],lambda node:{1:F(1)})
def strategy(node):
 p=F(1,4) if node.audit()['holes'][1][0]==48 else F(1,2)
 return {0:p,1:1-p}
bayes=value([([48,49],F(1,4)),([44,45],F(3,4))],[0],strategy,counterfactual_player=0)
s=n.Solver(g,.6,17,True,True,.1)
for _ in range(20000):s.run_iteration()
p=immutable_average_policy(n,s);node=n.NativeState(g)
for c in [0,5,48,49]:node.apply_action(c)
before=p(node);s.run_iteration();after=p(node);assert before==after
result={'river':river,'bayes':bayes,'snapshot_policy':before,'snapshot_after_training':after,'snapshot_stable':True}
def exact(x):
 if isinstance(x,F):return {'numerator':x.numerator,'denominator':x.denominator}
 if isinstance(x,dict):return {str(k):exact(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [exact(v) for v in x]
 return x
body=exact(result);raw=json.dumps(body,sort_keys=True,separators=(',',':')).encode();print(json.dumps({'canonical_sha256':hashlib.sha256(raw).hexdigest(),'result':body},indent=2))
