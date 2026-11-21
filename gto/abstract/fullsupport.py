"""Fixed learned continuations and a full-support class-pair expectation oracle."""
import base64,ctypes as C,hashlib,itertools,json,math,random,struct,subprocess,zlib
from pathlib import Path
from gto.abstract import model,call_reach as cr,call_study as cs,street_tree as st,root_interval as ri,gap_models as gm
from gto.abstract.continuation_learning import key
from gto.abstract.flop_conditional import Observation
from gto.abstract.factorial_transfer import category
from gto.abstract.flop_exact import U16
from gto.abstract.model import ints,doubles,IP,DP
S=169*169;WMAX=22100/17296

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def pack(values):
 raw=struct.pack('<'+str(len(values))+'d',*values);return {'codec':'f64le-zlib-base64','count':len(values),'sha256':hashlib.sha256(raw).hexdigest(),'data':base64.b64encode(zlib.compress(raw,6)).decode()}
def unpack(obj):
 raw=zlib.decompress(base64.b64decode(obj['data']));n=obj['count']
 if obj['codec']!='f64le-zlib-base64' or len(raw)!=8*n or hashlib.sha256(raw).hexdigest()!=obj['sha256']:raise ValueError('numeric packet checksum/shape')
 return list(struct.unpack('<'+str(n)+'d',raw))
def build(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);out=root/'fullsupport.so';subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(Path(__file__).with_name('fullsupport_native.cc')),'-o',str(out)],check=True);lib=C.CDLL(str(out.resolve()));lib.fullsupport.argtypes=[C.c_int,C.c_int,IP,IP,IP,U16,U16,DP,DP,IP,DP,DP];lib.fullsupport.restype=C.c_int;lib.oracle_update.argtypes=[C.c_int,C.c_int,DP,DP,DP,DP,DP];lib.oracle_update.restype=C.c_int;lib.scalar_update.argtypes=[C.c_int,C.c_int,C.c_int,DP,DP,DP,DP,DP,DP,DP];lib.scalar_update.restype=C.c_int;return lib

def groups(m):
 out=[]
 for h in m['pairs']:
  bits=key(Observation(tuple(h),tuple(m['flop']),0,2.,49.))[-3:];out.append(int(bits[0])*4+int(bits[1])*2+int(bits[2]))
 return out

def leaves(pi):
 return [cr.extract(pi,r['history'],'leaf'+str(r['leaf'])) for r in cr.leaf_ledger(pi) if r['matched']]

def game(r,fractions,mass,equity):
 t=st.tree(r['post_call_pot_bb'],r['remaining_stack_bb'],r['hero_actor'],fractions);off=[0]
 for n in t['nodes']:off.append(off[-1]+(0 if n['actor']<0 else 8*len(n['actions'])))
 return {'h':8,'v':8,'tree':t,'offsets':off,'mass':mass,'equity':equity,'game':{}}

def teacher(env,p,boards):
 # Within each public texture, uniform proposal makes raw reached moments the
 # correct self-normalized empirical conditional game. No actual opponent cards.
 pools={};ranges=leaves(env[3])
 for row in boards:
  m=cs.exact.matrix(env[0],row['cards']);g=groups(m)
  for r in ranges:
   if r['remaining_stack_bb']==0:continue
   out=(C.c_double*128)();status=env[1].type_aggregate(m['n'],8,8,m['cards'],ints(m['labels']),ints(g),ints(g),m['win'],m['tie'],doubles(r['hero_reach']),doubles(r['villain_reach']),out)
   if status:raise ValueError('teacher private chance')
   z=gm.direct_mass(env[5],r,row['cards']);k=str(r['leaf_index'])+'|'+row['category'];pool=pools.setdefault(k,[0.]*128)
   for i,v in enumerate(out):pool[i]+=v*z
 profiles={};metrics=[]
 for name,fractions in p['variants'].items():
  profiles[name]={}
  for r in ranges:
   if r['remaining_stack_bb']==0:continue
   for cat in sorted({b['category'] for b in boards}):
    k=str(r['leaf_index'])+'|'+cat;mom=pools[k];z=math.fsum(mom[::2]);g=game(r,fractions,[v/z for v in mom[::2]],[v/z for v in mom[1::2]]);policy,metric=st.trajectory(env[-1],g,st.uniform(g),[p['teacher']['iterations']])[0];profiles[name][k]=policy;metrics.append({'variant':name,'leaf':r['leaf_index'],'category':cat,'metrics':metric})
 return {'profiles':profiles,'metrics':metrics,'ranges':ranges,'scope':'fixed coarse own/public continuation policies;NOT complete poker equilibrium','frozen_policy_digest':env[4],'full_game_gto_verified':False}

def coefficients(teacher,p,cat,lib):
 aa=[];bb=[];bounds=[];names=[]
 for name,fractions in p['variants'].items():
  for r in teacher['ranges']:
   names.append((name,r['leaf_index']))
   if r['remaining_stack_bb']==0:a=[-50.]*64;b=[100.]*64
   else:
    g=game(r,fractions,[1/64]*64,[.5/64]*64);a,b=ri.coefficients(lib,g,teacher['profiles'][name][str(r['leaf_index'])+'|'+cat])
    if r['hero_actor']==1:a,b=[-a[j*8+i]-b[j*8+i] for i in range(8) for j in range(8)],[b[j*8+i] for i in range(8) for j in range(8)]
   aa.extend(a);bb.extend(b);bounds.append(max(max(abs(x),abs(x+y)) for x,y in zip(a,b)))
 return aa,bb,bounds,names

def evaluate_flop(native,rank,flop,coef):
 m=cs.exact.matrix(rank,flop);a,b,_,names=coef;n=len(names);out=(C.c_double*(n*S))();mass=(C.c_double*S)();g=groups(m)
 if native.fullsupport(m['n'],n,m['cards'],ints(m['labels']),ints(g),m['win'],m['tie'],doubles(a),doubles(b),ints(ri.full_counts()),out,mass):raise ValueError('full-support oracle aggregation')
 return list(out),list(mass)

def empirical_interval(mean,var,n,bound,c,delta):
 if n<2 or not 0<delta<1 or bound<0 or var<0 or abs(c)>bound+1e-7:raise ValueError('bounded IID sample interval')
 width=2*bound*WMAX;radius=math.sqrt(2*var*math.log(4/delta)/n)+7*width*math.log(4/delta)/(3*(n-1));lo=max(-bound,mean-radius-1e-7);hi=min(bound,mean+radius+1e-7)
 return lo,hi,radius

def oracle(env,native,coefs,draws,pilot,bounds,cache_dir,identity,delta):
 planes=len(bounds);count=len(draws);means_native=(C.c_double*(planes*S))();m2=(C.c_double*(planes*S))();control=doubles(pilot);unique=set();cached=0
 for index,flop in enumerate(draws):
  k=digest({'identity':identity,'flop':flop});path=cache_dir/(k+'.json');cat=category(flop)
  if path.exists():
   row=json.loads(path.read_text())
   if row['identity']!=identity or row['flop']!=flop:raise ValueError('oracle cache identity')
   y=unpack(row['payoff']);mass=unpack(row['mass']);cached+=1
  else:
   y,mass=evaluate_flop(native,env[0],flop,coefs[cat]);cache_dir.mkdir(parents=True,exist_ok=True);temp=path.with_suffix('.tmp');temp.write_text(json.dumps({'identity':identity,'flop':flop,'payoff':pack(y),'mass':pack(mass)},sort_keys=True,separators=(',',':'))+'\n');temp.replace(path)
  if native.oracle_update(planes,index+1,doubles(y),doubles(mass),control,means_native,m2):raise ValueError('oracle stable accumulation')
  unique.add(tuple(flop))
  if (index+1)%32==0:print(json.dumps({'oracle_samples_complete':index+1,'total':count,'cached':cached}),flush=True)
 means=list(means_native);variance=[max(0.,v/(count-1)) for v in m2];lower=[];upper=[];point=[];empty=0;clipped=0
 for plane,bound in enumerate(bounds):
  for j in range(S):
   k=plane*S+j;lo,hi,_=empirical_interval(means[k],variance[k],count,bound,pilot[k],delta)
   if lo>hi:empty+=1
   v=max(-bound,min(bound,means[k]));clipped+=int(v!=means[k]);point.append(v);lower.append(lo);upper.append(hi)
 # All-in same-class expected netEV is exactly0 by seat-swap symmetry.
 for plane,(_,leaf) in enumerate(coefs[next(iter(coefs))][3]):
  if model.tree()[leaf]['value']==100:
   for h in range(169):k=plane*S+h*169+h;point[k]=lower[k]=upper[k]=0.
 return {'point':pack(point),'lower':pack(lower),'upper':pack(upper),'samples':count,'unique_physical_flops':len(unique),'exact_board_fraction':len(unique)/22100,'counterfactual_estimator_support':'all169x169,all9matched leaves;not100%exactboard enumeration','empty_intervals':empty,'physical_point_clips':clipped,'model_bounds_bb':bounds,'delta_per_cell':delta,'target':'fixed learned continuation policies; uniform-fullsupport importance expectation','full_game_gto_verified':False}

def payoff_planes(oracle,teacher,variant,names):
 arrays={k:unpack(oracle[k]) for k in ('point','lower','upper')};nodes=model.tree();result={}
 for kind,data in arrays.items():
  values=[0.]*(len(nodes)*S)
  for i,node in enumerate(nodes):
   if node['actor']>=0:continue
   if node['matched']:
    plane=names.index((variant,i));values[i*S:(i+1)*S]=[2*v for v in data[plane*S:(plane+1)*S]]
   else:values[i*S:(i+1)*S]=[float(node['value'])]*S
  result[kind]=values
 return result
