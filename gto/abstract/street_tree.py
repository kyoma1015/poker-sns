"""Own-type/public-history behavioral CFR with one-raise flop abstraction."""
import ctypes as C
import math,subprocess
from pathlib import Path
from gto.abstract.model import ints,doubles,IP,DP
from gto.abstract import gap_models as gm
LEGACY=((0,0,1,1),(1,0,1,1),(1,1,1,1),(1,0,0,0),(0,0,0,0))


def tree(pot,remaining,hero_actor,fractions):
 if not fractions or hero_actor not in (0,1) or not math.isfinite(pot+remaining) or min(pot,remaining)<=0 or any(not math.isfinite(f) or f<=0 for f in fractions):raise ValueError('explicit finite HU street required')
 amounts=sorted(set(min(remaining,max(1.,pot*f)) for f in fractions));nodes=[]
 def terminal(paid,history,winner=None):
  i=len(nodes);h,v=paid[hero_actor],paid[1-hero_actor];c0=(-h-pot/2 if winner is None else pot/2+v if winner==hero_actor else -pot/2-h);nodes.append({'actor':-1,'seat':-1,'kind':'terminal','actions':[],'children':[],'history':history,'c0':c0,'c1':pot+h+v if winner is None else 0.});return i
 def node(seat,kind,paid,history,bet=0,raiser=None):
  i=len(nodes);n={'actor':0 if seat==hero_actor else 1,'seat':seat,'kind':kind,'paid':list(paid),'bet':bet,'actions':[],'children':[],'history':history,'c0':0.,'c1':0.};nodes.append(n)
  def add(action,construct):
   a=len(n['actions']);n['actions'].append(action);n['children'].append(construct([*history,(i,a)]))
  if kind=='open':
   if seat==1:add({'kind':'check'},lambda h:node(0,'open',paid,h))
   else:add({'kind':'check'},lambda h:terminal(paid,h))
   for b in amounts:
    nextpaid=list(paid);nextpaid[seat]=b
    add({'kind':'bet','amount':b},lambda h,b=b,np=nextpaid:node(1-seat,'face_bet',np,h,b))
  elif kind=='face_bet':
   add({'kind':'fold'},lambda h:terminal(paid,h,1-seat));matched=[bet,bet];add({'kind':'call'},lambda h:terminal(matched,h));r=min(3*bet,remaining)
   if r>bet+1e-12:
    if r<2*bet-1e-12 and abs(r-remaining)>1e-12:raise ValueError('non-all-in underraise')
    np=list(paid);np[seat]=r;add({'kind':'raise','amount':r},lambda h:node(1-seat,'face_raise',np,h,bet,seat))
  else:
   add({'kind':'fold'},lambda h:terminal(paid,h,1-seat));r=max(paid);add({'kind':'call'},lambda h:terminal([r,r],h))
  return i
 node(1,'open',[0.,0.],[]);return {'nodes':nodes,'pot':pot,'remaining':remaining,'hero_actor':hero_actor,'bet_amounts':amounts,'scope':'one street,one raise,turn/river check-through;NOTfullNLHE'}


def build(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);src=Path(__file__).with_suffix('.cc');dest=root/'street-tree.so';subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(src),'-o',str(dest)],check=True);lib=C.CDLL(str(dest.resolve()));args=[C.c_int,C.c_int,C.c_int,IP,IP,IP,DP,DP,DP,DP,DP];lib.street_evaluate.argtypes=[*args,DP];lib.street_evaluate.restype=C.c_int;lib.street_train.argtypes=[*args,C.c_int,C.c_int,DP,DP,DP,DP];lib.street_train.restype=C.c_int;return lib


def prepare(aggregate_lib,m,g,tree_spec):
 h,v=len(g['hkeys']),len(g['vkeys']);out=(C.c_double*(h*v*2))()
 if aggregate_lib.type_aggregate(m['n'],h,v,m['cards'],ints(m['labels']),ints(g['pair_hi']),ints(g['pair_vi']),m['win'],m['tie'],doubles(g['hero_reach']),doubles(g['villain_reach']),out):raise ValueError('street chance aggregation failed')
 nodes=tree_spec['nodes'];offsets=[0]
 for n in nodes:offsets.append(offsets[-1]+(0 if n['actor']<0 else h if n['actor']==0 else v)*len(n['actions']))
 return {'game':g,'tree':tree_spec,'h':h,'v':v,'offsets':offsets,'mass':[out[2*i] for i in range(h*v)],'equity':[out[2*i+1] for i in range(h*v)]}


def uniform(prepared):
 out=[]
 for n in prepared['tree']['nodes']:
  if n['actor']<0:continue
  types=prepared['h'] if n['actor']==0 else prepared['v'];out.extend([1/len(n['actions'])]*(types*len(n['actions'])))
 return out


def legacy_action(plan,node,spec):
 if node['kind']=='open':
  if not plan[0]:return next(i for i,a in enumerate(node['actions']) if a['kind']=='check')
  amount=min(spec['remaining'],max(1.,spec['pot']*.5));return min((i for i,a in enumerate(node['actions']) if a['kind']=='bet'),key=lambda i:abs(node['actions'][i]['amount']-amount))
 if node['kind']=='face_bet':
  if plan[1] and any(a['kind']=='raise' for a in node['actions']):kind='raise'
  else:kind='call' if plan[2] else 'fold'
 else:kind='call' if plan[3] else 'fold'
 return next(i for i,a in enumerate(node['actions']) if a['kind']==kind)


def lift_legacy(policy,prepared,plans=LEGACY):
 spec=prepared['tree'];g=prepared['game'];out=[]
 for node in spec['nodes']:
  if node['actor']<0:continue
  keys=g['hkeys'] if node['actor']==0 else g['vkeys']
  for key in keys:
   weights=[]
   for a,w in enumerate(policy.table[key]):
    possible=all(spec['nodes'][pn]['seat']!=node['seat'] or legacy_action(plans[a],spec['nodes'][pn],spec)==pa for pn,pa in node['history']);weights.append(w if possible else 0.)
   z=math.fsum(weights);row=[0.]*len(node['actions'])
   if z:
    for a,w in enumerate(weights):row[legacy_action(plans[a],node,spec)]+=w/z
   else:row=[1/len(row)]*len(row)
   out.extend(row)
 return out


def extend_half(half_policy,half,multi):
 out=[];old=half['tree'];new=multi['tree'];g=multi['game']
 for node in new['nodes']:
  if node['actor']<0:continue
  options=[(i,n) for i,n in enumerate(old['nodes']) if n['seat']==node['seat'] and n['kind']==node['kind']];idx,source=min(options,key=lambda x:(abs(x[1].get('bet',0)-node.get('bet',0)),x[1].get('bet',0)));types=multi['h'] if node['actor']==0 else multi['v']
  own_nonhalf=any(new['nodes'][pn]['seat']==node['seat'] and new['nodes'][pn]['actions'][pa]['kind']=='bet' and abs(new['nodes'][pn]['actions'][pa]['amount']-min(new['remaining'],max(1.,new['pot']*.5)))>1e-12 for pn,pa in node['history'])
  for t in range(types):
   row=[0.]*len(node['actions'])
   if own_nonhalf:row=[1/len(row)]*len(row)
   else:
    values=half_policy[half['offsets'][idx]+t*len(source['actions']):half['offsets'][idx]+(t+1)*len(source['actions'])]
    for act,w in zip(source['actions'],values):
     kind=act['kind']
     if kind=='bet':targets=[i for i,a in enumerate(node['actions']) if a['kind']=='bet'];j=min(targets,key=lambda i:abs(node['actions'][i]['amount']-act['amount']))
     elif kind=='raise' and not any(a['kind']=='raise' for a in node['actions']):j=next(i for i,a in enumerate(node['actions']) if a['kind']=='call')
     else:j=next(i for i,a in enumerate(node['actions']) if a['kind']==kind)
     row[j]+=w
   out.extend(row)
 return out


def _args(prepared,policy):
 nodes=prepared['tree']['nodes'];h,v=prepared['h'],prepared['v']
 if len(policy)!=prepared['offsets'][-1] or len(prepared['mass'])!=h*v or len(prepared['equity'])!=h*v:raise ValueError('street strategy/moment dimensions differ')
 for i,n in enumerate(nodes):
  if n['actor']<0:continue
  types=h if n['actor']==0 else v
  for t in range(types):
   row=policy[prepared['offsets'][i]+t*len(n['actions']):prepared['offsets'][i]+(t+1)*len(n['actions'])]
   if any(not math.isfinite(x) or x<0 for x in row) or not math.isclose(math.fsum(row),1,abs_tol=1e-10):raise ValueError('normalized own-info behavioral row required')
 return [len(nodes),h,v,ints([n['actor'] for n in nodes]),ints([len(n['actions']) for n in nodes]),ints([c for n in nodes for c in (n['children']+[-1]*4)[:4]]),doubles([n['c0'] for n in nodes]),doubles([n['c1'] for n in nodes]),doubles(prepared['mass']),doubles(prepared['equity']),doubles(policy)]


def _metrics(out):
 value,upper,lower,nc=out[:4]
 if min(upper-value,value-lower,nc)<-1e-7:raise ValueError('private-info BR interval failed')
 return {'profile_hero_ev_bb':value,'hero_br_ev_bb':upper,'villain_br_hero_ev_bb':lower,'restricted_nashconv_bb':max(0.,nc),'restricted_exploitability_bb':max(0.,nc)/2,'full_game_gto_verified':False,'sampling_error_fixed_board_bb':0}


def evaluate(lib,prepared,policy):
 out=(C.c_double*4)()
 if lib.street_evaluate(*_args(prepared,policy),out):raise ValueError('invalid behavioral game/strategy')
 return _metrics(out)


def trajectory(lib,prepared,prior,budgets):
 if not budgets or sorted(set(budgets))!=list(budgets) or any(type(t) is not int or not 1<=t<=1000000 for t in budgets):raise ValueError('fixed increasing bounded checkpoints required')
 size=len(prior);reg=(C.c_double*size)();sums=(C.c_double*size)();avg=(C.c_double*size)();out=(C.c_double*5)();start=0;results=[];args=_args(prepared,prior)
 for stop in budgets:
  if lib.street_train(*args,start,stop,reg,sums,avg,out):raise ValueError('CFR update failed')
  metric=_metrics(out);bound=out[4]
  if metric['restricted_nashconv_bb']>bound+1e-7:raise ValueError('CFR counterfactual regret certificate failed')
  metric.update(iterations=stop,positive_counterfactual_regret_bound_bb=bound,averaging='own-realization weighted; simultaneous counterfactual updates');results.append((list(avg),metric));start=stop
 return results
