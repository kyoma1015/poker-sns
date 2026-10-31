from fractions import Fraction as F
import importlib,os,sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()));sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR'])
from gto.native.belief_observation import condition_public_cards,infoset_consistent_policy,evaluate_observation
from gto.native.training import NativeGame
n=importlib.import_module('pokerid_g12');g=NativeGame([4,4]);deals=[([48,49],F(1,4)),([40,45],F(3,4))]
conditioned=condition_public_cards([0,5],deals,[48,8,17])
river=evaluate_observation(n,g,[0,5],deals,[1,8,17,26,35],[1,1,1,8,17,1,1,26,1,1,35,1,1],lambda s:{1:F(1)})
state=n.NativeState(g)
for action in [0,5,40,45,1,1,48,8,17]:state.apply_action(action)
shove=max(state.legal_actions());aggressor=state.current_player()
def policy(node):
 if not node.audit()['board']:return {1:F(1)}
 return {max(node.legal_actions()):F(1)} if node.current_player()==aggressor else {0:F(1)}
filtered=evaluate_observation(n,g,[0,5],deals,[48,8,17],[1,1,48,8,17,shove,0],policy)
def spy(node):return {0:F(1)} if node.audit()['holes'][1][0]==48 else {1:F(1)}
checked=infoset_consistent_policy(spy);refused=False
for cards in [[48,49],[40,45]]:
 node=n.NativeState(g)
 for c in [0,5]+cards:node.apply_action(c)
 try:checked(node)
 except ValueError:refused=True
assert refused
body={'conditioned':conditioned,'river':river,'filtered':filtered,'hidden_card_policy_refused':refused}
def exact(x):
 if isinstance(x,F):return {'numerator':x.numerator,'denominator':x.denominator}
 if isinstance(x,dict):return {str(k):exact(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [exact(v) for v in x]
 return x
result=exact(body);raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode();print(json.dumps({'canonical_sha256':hashlib.sha256(raw).hexdigest(),'result':result},indent=2))
