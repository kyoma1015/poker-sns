"""Exact public-prefix CALL/check reach, without editing frozen preflop CFR."""
import hashlib,math
from gto.abstract import model,range_features as feature
from gto.abstract.precision import frozen_rows
from gto.abstract.generalization_features import uniform_strength


def extract(policy,history,stage):
 nodes=model.tree();n=169
 if len(policy)!=len(nodes)*3*n:raise ValueError('complete frozen strategy required')
 frozen_rows(policy,nodes,n);seat=[[1.]*n,[1.]*n];index=0;parent=None
 for action in history:
  node=nodes[index]
  if node['actor']<0 or action not in node['actions']:raise ValueError('legal complete public prefix required')
  a=node['actions'].index(action);actor=node['actor'];weights=policy[(index*3+a)*n:(index*3+a+1)*n];seat[actor]=[x*y for x,y in zip(seat[actor],weights)];parent=index;index=node['children'][a]
 terminal=nodes[index]
 if parent is None or terminal['actor']!=-1 or not terminal['matched']:raise ValueError('prefix must end at matched CALL/check terminal')
 actor=nodes[parent]['actor'];pot=float(terminal['value']);_,chance=model.chance(model.classes());mass=math.fsum(chance[i*n+j]*seat[0][i]*seat[1][j] for i in range(n) for j in range(n))
 if not 0<mass<=1 or not 0<pot<=100:raise ValueError('positive reached matched pot required')
 return {'stage':stage,'node_index':parent,'leaf_index':index,'hero_actor':actor,'history':list(history),'hero_reach':seat[actor],'villain_reach':seat[1-actor],'seat_reach':seat,'conditional_mass':mass,'post_call_pot_bb':pot,'matched_contribution_bb':pot/2,'remaining_stack_bb':50-pot/2,'spr':(50-pot/2)/pot,'frozen_strategy':True,'conditioned_on_call':True,'policy_digest':hashlib.sha256(model.doubles(policy)).hexdigest()}


def book(lib,m,reach):
 opponents={reach['hero_actor']:reach['villain_reach'],1-reach['hero_actor']:reach['hero_reach']}
 return {'uniform':uniform_strength(m),'by_actor':{a:feature.conditional(lib,m,r) for a,r in opponents.items()},'public_history':reach['history'],'actual_opponent_cards_required':False}


def leaf_ledger(policy):
 nodes=model.tree();n=169;frozen_rows(policy,nodes,n);_,chance=model.chance(model.classes());rows=[]
 def walk(index,seat,history):
  node=nodes[index]
  if node['actor']<0:
   mass=math.fsum(chance[i*n+j]*seat[0][i]*seat[1][j] for i in range(n) for j in range(n));rows.append({'leaf':index,'history':history,'matched':node['matched'],'probability':mass,'fold_sb_payoff_bb':None if node['matched'] else node['value']/2});return
  actor=node['actor']
  for a,c in enumerate(node['children']):
   r=[list(seat[0]),list(seat[1])];r[actor]=[x*y for x,y in zip(seat[actor],policy[(index*3+a)*n:(index*3+a+1)*n])];walk(c,r,history+[node['actions'][a]])
 walk(0,[[1.]*n,[1.]*n],[])
 if not math.isclose(math.fsum(x['probability'] for x in rows),1,abs_tol=1e-12):raise ValueError('terminal probability conservation')
 return rows
