"""Independent postflop deviations of fixed research preflop profiles,not GTO admission."""
import argparse,ctypes as C,json,math,subprocess
from pathlib import Path
from gto.abstract import model,fullsupport as fs,call_study as cs,call_reach as cr,gap_models as gm,street_tree as st,suit_exact as old
from gto.abstract.factorial_transfer import category
from gto.abstract.model import ints,doubles,IP,DP
from gto.abstract.range_study import sha
ROOT=Path('docs/qa/continuation-audit-20261106');P=ROOT/'protocol.json';D=ROOT/'design.json';H=169*8;S=H*8

def sources():return {**old.sources(),**{f:sha(Path(__file__).with_name(f)) for f in ('continuation_audit.py','continuation_audit.cc','continuation_audit_br.py')}}
def inputs():
 p=json.loads(P.read_text());f=json.loads((old.ROOT/'results.json').read_text());configs={}
 for variant in p['preflop_profiles']:
  for stage,history in p['stages'].items():configs[variant+'|'+stage]=cr.extract(f['complete_preflop_policies'][variant],history,stage)
 return p,f,configs

def design():
 p,f,c=inputs();return {'protocol_sha256':sha(P),'source_sha256':sources(),'preflop_result_sha256':sha(old.ROOT/'results.json'),'teacher_sha256':sha(old.old.TEACHER),'orbits':json.loads(old.DESIGN.read_text())['orbits'],'configs':c,'selection_performed':False,'formal_acceptance':0}
def check():
 d=json.loads(D.read_text())
 if d['source_sha256']!=sources() or d['protocol_sha256']!=sha(P) or d['preflop_result_sha256']!=sha(old.ROOT/'results.json') or d['teacher_sha256']!=sha(old.old.TEACHER):raise ValueError('fixed audit design changed')
 return d

def build(root):
 root.mkdir(parents=True,exist_ok=True);target=root/'audit.so';subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(Path(__file__).with_suffix('.cc')),'-o',str(target)],check=True);lib=C.CDLL(str(target.resolve()));a=[C.c_int,C.c_int,C.c_int,IP,IP,IP,DP,DP,DP,DP,DP];lib.street_evaluate.argtypes=[*a,DP];lib.street_train.argtypes=[*a,C.c_int,C.c_int,DP,DP,DP,DP];return lib

def expanded_tree(pot,remaining,hero_actor,fractions):
 ns=[];amounts=sorted(set(min(remaining,max(1.,pot*x)) for x in fractions))
 def terminal(paid,history,winner=None):
  i=len(ns);h,v=paid[hero_actor],paid[1-hero_actor];ns.append({'actor':-1,'seat':-1,'actions':[],'children':[],'history':history,'c0':-h-pot/2 if winner is None else pot/2+v if winner==hero_actor else -pot/2-h,'c1':pot+h+v if winner is None else 0.});return i
 def node(seat,kind,paid,history,bet=0.,increment=0.,raises=0):
  i=len(ns);n={'actor':0 if seat==hero_actor else 1,'seat':seat,'kind':kind,'paid':list(paid),'bet':bet,'actions':[],'children':[],'history':history,'c0':0.,'c1':0.};ns.append(n)
  def add(action,fn):a=len(n['actions']);n['actions'].append(action);n['children'].append(fn(history+[(i,a)]))
  if kind=='open':
   add({'kind':'check'},lambda h:node(0,'open',paid,h) if seat==1 else terminal(paid,h))
   for b in amounts:
    np=list(paid);np[seat]=b;add({'kind':'bet','amount':b},lambda h,b=b,np=np:node(1-seat,'face_bet',np,h,b,b,0))
  else:
   add({'kind':'fold'},lambda h:terminal(paid,h,1-seat));add({'kind':'call'},lambda h:terminal([bet,bet],h));r=min(remaining,3*bet)
   if raises<2 and r>bet+1e-12:
    if r<bet+increment-1e-12 and abs(r-remaining)>1e-12:raise ValueError('illegal undersized nonallin raise')
    np=list(paid);np[seat]=r;add({'kind':'raise','amount':r},lambda h:node(1-seat,'face_raise',np,h,r,r-bet,raises+1))
  return i
 node(1,'open',[0.,0.],[]);return {'nodes':ns,'pot':pot,'remaining':remaining,'hero_actor':hero_actor,'bet_amounts':amounts,'scope':'expanded fixed flop sizes,two raises,turnriver checkthrough;not NLHE'}

def future_envelope(g,pi,m,e):
 ns=g['tree']['nodes'];h,v=g['h'],g['v'];known=unknown=0.
 def walk(k,rh,rv):
  nonlocal known,unknown
  n=ns[k]
  if n['actor']<0:
   mass=math.fsum(m[i*v+j]*rh[i]*rv[j] for i in range(h) for j in range(v))
   if 0<n['c1']<100-1e-10:unknown+=mass
   else:known+=math.fsum((n['c0']*m[i*v+j]+n['c1']*e[i*v+j])*rh[i]*rv[j] for i in range(h) for j in range(v))
   return
  for a,c in enumerate(n['children']):
   if n['actor']==0:walk(c,[x*pi[g['offsets'][k]+i*len(n['actions'])+a] for i,x in enumerate(rh)],rv)
   else:walk(c,rh,[x*pi[g['offsets'][k]+j*len(n['actions'])+a] for j,x in enumerate(rv)])
 walk(0,[1.]*h,[1.]*v);return {'known_root_EV':known,'unresolved_showdown_probability':unknown,'root_lower':known-50*unknown,'root_upper':known+50*unknown}

def game(r,fractions,owner,h=8,v=8,expanded=False):
 tree=(expanded_tree if expanded else st.tree)(r['post_call_pot_bb'],r['remaining_stack_bb'],owner,fractions);off=[0]
 for n in tree['nodes']:off.append(off[-1]+(0 if n['actor']<0 else (h if n['actor']==0 else v)*len(n['actions'])))
 return {'h':h,'v':v,'tree':tree,'offsets':off}
def expand(g,coarse):
 out=[];pos=0
 for node in g['tree']['nodes']:
  if node['actor']<0:continue
  n=len(node['actions']);types=g['h'] if node['actor']==0 else g['v']
  for t in range(types):out.extend(coarse[pos+(t%8)*n:pos+(t%8+1)*n])
  pos+=8*n
 if pos!=len(coarse):raise ValueError('same public tree required for own-information policy expansion')
 return out

def args(g,policy,m,e):
 ns=g['tree']['nodes'];return [len(ns),g['h'],g['v'],ints([x['actor'] for x in ns]),ints([len(x['actions']) for x in ns]),ints([c for x in ns for c in (x['children']+[-1]*12)[:12]]),doubles([x['c0'] for x in ns]),doubles([x['c1'] for x in ns]),doubles(m),doubles(e),doubles(policy)]
def evaluate(lib,g,policy,m,e):
 out=(C.c_double*4)()
 if lib.street_evaluate(*args(g,policy,m,e),out):raise ValueError('valid joint chance/own policy required')
 return st._metrics(out)
def train(lib,g,m,e,budgets):
 pi=[1/len(n['actions']) for n in g['tree']['nodes'] if n['actor']>=0 for _ in range(8) for _a in n['actions']];a=args(g,pi,m,e);size=len(pi);reg=(C.c_double*size)();sums=(C.c_double*size)();avg=(C.c_double*size)();out=(C.c_double*5)();start=0;trace=[]
 for stop in budgets:
  if lib.street_train(*a,start,stop,reg,sums,avg,out):raise ValueError('expanded CFR failed')
  metric=st._metrics(out);metric.update(iterations=stop,regret_bound_bb=out[4]);trace.append(metric);start=stop
  if metric['restricted_nashconv_bb']>out[4]+1e-7:raise ValueError('regret certificate mismatch')
 return list(avg),trace

def packet_path(cache,row,d):return cache/(fs.digest({'source':d['source_sha256'],'preflop':d['preflop_result_sha256'],'protocol':d['protocol_sha256'],'flop':row['representative']})+'.json')
def moments(root,cache,parity):
 d=check();env=cs.setup(root);cache.mkdir(parents=True,exist_ok=True)
 for k,row in enumerate(d['orbits']):
  if k%2!=parity:continue
  path=packet_path(cache,row,d)
  if path.exists():continue
  m=cs.exact.matrix(env[0],row['representative']);groups=fs.groups(m);hi=[label*8+g for label,g in zip(m['labels'],groups)];data={}
  for name,r in d['configs'].items():
   z=gm.direct_mass(env[5],r,row['representative'])/(1624350*17296)
   for owner in (0,1):
    out=(C.c_double*(2*S))()
    if env[1].type_aggregate(m['n'],H,8,m['cards'],ints(m['labels']),ints(hi),ints(groups),m['win'],m['tie'],doubles(r['seat_reach'][owner]),doubles(r['seat_reach'][1-owner]),out):raise ValueError('enriched moment aggregation failed')
    data[name+'|'+str(owner)]=fs.pack([x*z for x in out])
  tmp=path.with_suffix('.tmp'+str(parity));tmp.write_text(json.dumps({'flop':row['representative'],'identity':d['source_sha256'],'data':data},sort_keys=True,separators=(',',':'))+'\n');tmp.replace(path)
  if k%32==parity:print(json.dumps({'moment_index':k,'parity':parity,'total':len(d['orbits'])}),flush=True)

def read(cache,row,d):
 obj=json.loads(packet_path(cache,row,d).read_text())
 if obj['identity']!=d['source_sha256'] or obj['flop']!=row['representative']:raise ValueError('moment identity')
 return {k:fs.unpack(v) for k,v in obj['data'].items()}
def coarse(mom):
 out=[0.]*128
 for i in range(H):
  for j in range(8):
   k=(i*8+j)*2;to=((i%8)*8+j)*2;out[to]+=mom[k];out[to+1]+=mom[k+1]
 return out
def normalized(mom):
 z=math.fsum(mom[::2])
 if z<=0:raise ValueError('positive posterior mass required')
 return z,[x/z for x in mom[::2]],[x/z for x in mom[1::2]]

def analyze(root,cache):
 d=check();p,f,configs=inputs();lib=build(root);teacher=json.loads(old.old.TEACHER.read_text());fractions=json.loads(old.old.P.read_text())['variants'];pools={}
 for row in d['orbits']:
  cat=category(row['representative'])
  for k,mom in read(cache,row,d).items():
   a=pools.setdefault(k+'|'+cat,[0.]*(2*S));mult=row['multiplicity']
   for i,v in enumerate(mom):a[i]+=v*mult
 profiles={};traces={};models=('fixed_small','fixed_large','posterior_small','posterior_large','posterior_union');cats=sorted({category(r['representative']) for r in d['orbits']});prepared={};summary={}
 from gto.abstract.continuation_audit_br import independent
 for name,r in configs.items():
  variant,stage=name.split('|');summary[name]={'root_call_probability':r['conditional_mass'],'models':{}}
  for modelname in models:
   mode='learned_'+modelname.split('_')[-1];frac=p['union_fractions'] if modelname.endswith('union') else fractions[mode];summary[name]['models'][modelname]={'texture_flags':{'profile':0.,'gain':0.},'texture_class_flags':{'profile':0.,'gain':0.},'board_class_flags':{'profile':0.,'gain':0.},'training':[],'future_street_envelope':{},'by_seat':{str(s):{} for s in (0,1)}}
   for cat in cats:
    key=name+'|0|'+cat;z,m,e=normalized(coarse(pools[key]));g=game(r,frac,0,expanded=modelname.endswith('union'))
    if modelname.startswith('fixed_'):pi=teacher['profiles'][mode][str(r['leaf_index'])+'|'+cat];trace=[]
    else:pi,trace=train(lib,g,m,e,p['training']['iterations'])
    profiles[name+'|'+modelname+'|'+cat]=pi;summary[name]['models'][modelname]['training'].append({'category':cat,'trace':trace})
    for owner in (0,1):
     key=name+'|'+str(owner)+'|'+cat;z,m,e=normalized(coarse(pools[key]));cg=game(r,frac,owner,expanded=modelname.endswith('union'));base=evaluate(lib,cg,pi,m,e);checkref=independent(cg,pi,m,e)
     if max(abs(base[k]-checkref[k]) for k in checkref)>1e-8:raise ValueError('independent coarse BR mismatch')
     eg=game(r,frac,owner,H,expanded=modelname.endswith('union'));ep=expand(eg,pi);zz,mm,ee=normalized(pools[key]);rich=evaluate(lib,eg,ep,mm,ee)
     if abs(base['profile_hero_ev_bb']-rich['profile_hero_ev_bb'])>1e-8:raise ValueError('refinement altered fixed profile')
     if rich['hero_br_ev_bb']+1e-8<base['hero_br_ev_bb']:raise ValueError('private information BR monotonicity')
     target=summary[name]['models'][modelname]
     for level,val in (('texture_flags',base),('texture_class_flags',rich)):
      entry=target['by_seat'][str(owner)].setdefault(level,{'profile_root_bb':0.,'gain_root_bb':0.});entry['profile_root_bb']+=z*val['profile_hero_ev_bb'];entry['gain_root_bb']+=z*(val['hero_br_ev_bb']-val['profile_hero_ev_bb'])
     if owner==0:
      envelope=future_envelope(cg,pi,m,e);future=target['future_street_envelope']
      for label,val in envelope.items():future[label]=future.get(label,0.)+z*val
     static=args(eg,ep,mm,ee);static[8]=static[9]=None;prepared[(name,modelname,cat,owner)]=(None,None,static)
 # Same fixed profiles evaluated with exact public board and enriched own-private information.
 for index,row in enumerate(d['orbits']):
  cat=category(row['representative']);data=read(cache,row,d)
  for name,r in configs.items():
   for owner in (0,1):
    z,m,e=normalized(data[name+'|'+str(owner)]);weight=z*row['multiplicity'];mc=doubles(m);ec=doubles(e)
    for modelname in models:
     g,pi,static=prepared[(name,modelname,cat,owner)];a=list(static);a[8]=mc;a[9]=ec;out=(C.c_double*4)()
     if lib.street_evaluate(*a,out):raise ValueError('exact board BR')
     entry=summary[name]['models'][modelname]['by_seat'][str(owner)].setdefault('board_class_flags',{'profile_root_bb':0.,'gain_root_bb':0.});entry['profile_root_bb']+=weight*out[0];entry['gain_root_bb']+=weight*(out[1]-out[0])
  if index%64==0:print(json.dumps({'BR_board_index':index,'total':len(d['orbits'])}),flush=True)
 for name,r in configs.items():
  variant,stage=name.split('|');target_call=f['models'][variant]['contexts'][stage];expected=math.fsum(x['reach_mass']*x['frequencies'][1]*x['action_ev_bb'][1] for x in target_call['hands'].values());prob=math.fsum(math.fsum(pools[name+'|0|'+cat][::2]) for cat in cats)
  if abs(prob-r['conditional_mass'])>1e-10:raise ValueError('true board/root reach normalization')
  for modelname,record in summary[name]['models'].items():
   for owner,vals in record['by_seat'].items():
    for level in ('texture_flags','texture_class_flags','board_class_flags'):
     record[level]['gain']+=vals[level]['gain_root_bb'];record[level]['profile']+=vals[level]['profile_root_bb'] # profiles from two seats should cancel
    if vals['board_class_flags']['gain_root_bb']+1e-8<vals['texture_class_flags']['gain_root_bb']:raise ValueError('public information BR monotonicity')
    if abs(vals['board_class_flags']['profile_root_bb']-vals['texture_flags']['profile_root_bb'])>1e-8:raise ValueError('public refinement changed fixed profile')
   if modelname=='fixed_'+variant.split('_')[-1]:
    val=record['by_seat'][str(r['hero_actor'])]['texture_flags']['profile_root_bb']
    if abs(val-expected)>1e-8:raise ValueError('published exact actionEV does not match new independent moments')
   for level in ('texture_flags','texture_class_flags','board_class_flags'):record[level]['conditional_call_nashconv_bb']=record[level]['gain']/prob
  summary[name]['root_probability_error']=abs(prob-r['conditional_mass']);summary[name]['published_profile_caller_root_bb']=expected
 return {'schema':'pokerid-continuation-audit-results-v1','protocol_sha256':sha(P),'source_sha256':sources(),'condition':f['condition'],'population':{'physical_flops':22100,'orbits':1755,'sampling_error':0},'configs':summary,'profiles':profiles,'formal_acceptance':0,'normal_gto_admission':False,'real_game_approximation_error':'UNKNOWN','external_gto_comparison':'NOT PERFORMED','scope':'postflop own/public-information restricted BR of frozen preflop profile;NOT fullgame GTO upperbound;later betting omitted'}

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--phase',choices=('design','moments','analyze'),required=True);a.add_argument('--output',type=Path);a.add_argument('--build-dir',type=Path);a.add_argument('--cache-dir',type=Path);a.add_argument('--parity',type=int,choices=(0,1));v=a.parse_args()
 if v.output and v.output.exists():a.error('fresh output required')
 if v.phase=='moments':moments(v.build_dir,v.cache_dir,v.parity)
 else:
  out=design() if v.phase=='design' else analyze(v.build_dir,v.cache_dir);v.output.parent.mkdir(parents=True,exist_ok=True);v.output.write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n');print('PASS',v.phase)
