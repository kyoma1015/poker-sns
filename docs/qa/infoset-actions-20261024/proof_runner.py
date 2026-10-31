from fractions import Fraction as F
import importlib,os,sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()));sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR'])
from gto.native.training import NativeGame
from gto.native.belief_observation import compare_hero_actions
n=importlib.import_module('pokerid_g12');g=NativeGame([4,4]);history=[1,1,1,8,17,1,1,26,1,1,35,1]
def calculate(deals,policy,actions=(1,4)):
 return compare_hero_actions(n,g,[0,5],deals,[1,8,17,26,35],history,list(actions),policy)
def fold_policy(s):
 if s.audit()['round']<3 or s.current_player()==0:return {1:F(1)}
 return {0:F(1)} if 0 in s.legal_actions() else {1:F(1)}
a=calculate([([48,49],F(1,4)),([40,45],F(3,4))],fold_policy)
b=calculate([([48,49],F(3,4)),([40,45],F(1,4))],lambda s:{1:F(1)})
z=calculate([([48,49],F(1,4)),([40,45],F(3,4))],lambda s:{0:F(1)} if 0 in s.legal_actions() else {1:F(1)})
def exact(x):
 if isinstance(x,F):return {'numerator':x.numerator,'denominator':x.denominator}
 if isinstance(x,dict):return {str(k):exact(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [exact(v) for v in x]
 return x
result=exact({'fold_continuation':a,'call_continuation':b,'zero_observation':z})
raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode();print(json.dumps({'canonical_sha256':hashlib.sha256(raw).hexdigest(),'result':result},indent=2))
