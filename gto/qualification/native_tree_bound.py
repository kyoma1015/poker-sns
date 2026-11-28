"""Native ledger/terminal-basis proof for a bounded public response tree.
Replays every offered native action, detects missing legal deviations, and proves
covered terminal utility for loss/tie/win. Missing chance/size/info proofs yield
UNKNOWN, never a substituted physical100BB convergence claim.
"""
import copy
from gto.qualification.native_mccfr import betting
from gto.qualification.policy import legal,act
from gto.qualification.integrated_br import transfer_bound

def verify(nodes,rules,stacks=(100,100)):
 missing=[];errors=[];leaf_count=0;max_error=0.;seen=set()
 def walk(k,b):
  nonlocal leaf_count,max_error
  if k in seen:raise ValueError('tree node reused; require explicit public histories')
  seen.add(k);n=nodes[k]
  if n['actor']<0:
   leaf_count+=1
   if not b.done:errors.append(dict(node=k,kind='uncertified continuation cut'));return
   for ranks,win in (([0,1],0.),([1,1],.5),([1,0],1.)):
    value=b.settle(ranks,True)['net'][0]/2;pred=n.get('c0',0)+n.get('c1',0)*win;max_error=max(max_error,abs(value-pred))
   return
  if b.done or b.actor!=n['actor'] or b.round!=n['round']:errors.append(dict(node=k,kind='native actor/round mismatch'));return
  offered=legal(b);actions=n['native_actions']
  if len(actions)!=len(n['children']) or len(set(actions))!=len(actions) or any(a not in offered for a in actions):raise ValueError('legal native sparse action tree')
  omitted=sorted(set(offered)-set(actions))
  if omitted:missing.append(dict(node=k,round=b.round,actor=b.actor,omitted=omitted))
  for a,c in zip(actions,n['children']):child=copy.deepcopy(b);act(child,a);walk(c,child)
 walk(0,betting(rules,stacks));valid=not errors and max_error<1e-10 and len(seen)==len(nodes)
 return dict(native_nodes=len(seen),terminal_nodes=leaf_count,covered_terminal_basis_exact=valid,max_terminal_basis_error=max_error,errors=errors,omitted=missing,complete_action_coverage=valid and not missing,covered_terminal_error_upper=0. if valid else None,full_native_chance_error_upper=None,full_native_information_error_upper=None,omitted_size_error_upper=None,full_native_NashConv_upper=transfer_bound(0.,continuation_uniform_error=None,chance_uniform_error=None,omitted_gains=None,information_gains=None),scope='exact on this native public tree; missing legal branches/chance/info stay UNKNOWN',formal_pass=False)
