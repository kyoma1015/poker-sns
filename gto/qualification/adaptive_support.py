"""Budgeted native legal-size expansion, selected from development CF residuals.
A priority is not an omitted-size bound. All downstream responses stay in the
same native public ledger. Unknown gains never become certified zero error.
"""
from gto.qualification import stream_chance as sc
from gto.qualification.native_mccfr import betting
from gto.qualification.policy import legal

def expand(rules,root_actions,residuals,*,max_new=1,max_nodes=6000,downstream=(23,)):
 if type(max_new) is not int or max_new<0 or max_nodes<1:raise ValueError('bounded size budget')
 offered=legal(betting(rules));root=set(root_actions)
 if not root.issubset(offered):raise ValueError('legal existing support required')
 candidates=sorted([r for r in residuals if r['action'] in offered and r['action'] not in root and r['action']>1 and r['CF_residual']>0],key=lambda r:(-r['CF_residual'],r['action']))
 accepted=[];rejected=[];nodes=sc.expanded_tree(rules,sorted(root),downstream)
 for row in candidates:
  if len(accepted)>=max_new:break
  try:new=sc.expanded_tree(rules,sorted(root|{row['action']}),downstream)
  except MemoryError:rejected.append(row['action']);continue
  if len(new)>max_nodes:rejected.append(row['action']);continue
  root.add(row['action']);nodes=new;accepted.append(row['action'])
 return nodes,dict(accepted=accepted,budget_rejected=rejected,support=sorted(root),legal_count=len(offered),omitted=len(set(offered)-root),complete_native_BR_upper=None,omitted_size_error_upper=None,formal_pass=False)
