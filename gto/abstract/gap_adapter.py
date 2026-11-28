"""Readonly class-leaf and root-attribution checks; never a full-poker EV.

Fresh local payoff arrays contain ONLY selected-board contribution at one CALL
leaf. Zero other leaves are linear-attribution placeholders, not a poker game.
No frozen policy update, original payoff-file overwrite or solver call occurs.
"""
import ctypes as C
import hashlib,math
from gto.abstract import model
from gto.abstract.model import ints,doubles
from gto.abstract import gap_models as gm


def leaf_check(aggregate_lib,reference_lib,m,g,policy,reference):
 if g['actions']!=4:raise ValueError('preserved four-arm leaf oracle only')
 p,q=gm.strategies(g,policy);f=gm.forms(reference_lib,4,g['hero_actor'],g['pot'],g['remaining'],g['fraction']);c0=[];c1=[]
 for h in p:
  for v in q:
   lo=math.fsum(h[a]*v[b]*f[a*4+b][0] for a in range(4) for b in range(4));hi=math.fsum(h[a]*v[b]*f[a*4+b][1] for a in range(4) for b in range(4));c0.append(lo);c1.append(hi-lo)
 out=(C.c_double*(169*169))();counts=(C.c_int*(169*169))()
 if aggregate_lib.type_leaf(m['n'],len(p),len(q),m['cards'],ints(m['labels']),ints(g['pair_hi']),ints(g['pair_vi']),m['win'],m['tie'],doubles(c0),doubles(c1),out,counts):raise ValueError('preserved class-leaf oracle failed')
 if list(counts)!=reference['compatible_class_pair_counts']:raise ValueError('class-pair coverage differs')
 return max(abs(a-b) for a,b in zip(out,reference['class_leaf_hero_net_bb']))


def add_partial(accum,reference,full_counts):
 for i,(value,count,denom) in enumerate(zip(reference['class_leaf_hero_net_bb'],reference['compatible_class_pair_counts'],full_counts)):
  if count and not denom:raise ValueError('impossible full chance cell')
  if denom:accum[i]+=value*count/(denom*17296)


def root_attribution(lib,policy,reach,partial_hero,conditional_selected_ev):
 before=hashlib.sha256(doubles(policy)).hexdigest();nodes=model.tree();n=169;target=nodes[reach['node_index']];leaf=target['children'][target['actions'].index('call')]
 if nodes[leaf]['actor']!=-1 or not nodes[leaf]['matched']:raise ValueError('expected frozen matched CALL leaf')
 actor=reach['hero_actor'];sign=1 if actor==0 else -1;values=[0.]*(len(nodes)*n*n)
 for h in range(n):
  for v in range(n):
   pos=h*n+v if actor==0 else v*n+h;values[leaf*n*n+pos]=2*sign*partial_hero[h*n+v]
 _,probability=model.chance(model.classes());ev=(C.c_double*(len(nodes)*3*n))();r=(C.c_double*(len(nodes)*n))();metrics=(C.c_double*4)()
 status=lib.abstract_evaluate(n,len(nodes),ints([x['actor'] for x in nodes]),ints([len(x['actions']) for x in nodes]),ints([c for x in nodes for c in (x['children']+[-1]*3)[:3]]),doubles(probability),doubles(values),doubles(policy),ev,r,metrics)
 if status:raise ValueError('readonly frozen policy evaluation failed')
 after=hashlib.sha256(doubles(policy)).hexdigest()
 if before!=after:raise ValueError('frozen policy changed')
 manual=reach['conditional_mass']*sign*conditional_selected_ev;native=metrics[0]/2
 return {'native_root_selected_contribution_sb_bb':native,'manual_root_selected_contribution_sb_bb':manual,'absolute_error_bb':abs(native-manual),'frozen_policy_digest_before':before,'frozen_policy_digest_after':after,'policy_updated':False,'call_leaf_index':leaf,'all_other_leaves':'ZERO FOR LINEAR ATTRIBUTION ONLY; not a complete poker payoff','not_full_game_ev':True,'unused_br_metrics_not_gto_evidence':True}
