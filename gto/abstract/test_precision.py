import ctypes as C,itertools,json,math,os,random,tempfile,unittest
from pathlib import Path
from gto.abstract.model import IP,ints,load,rank,classes,chance,tree
from gto.abstract.precision_runouts import load as fast_load,exact,canonical
from gto.abstract.precision_archive import unpack
from gto.abstract.precision import integrate_action,bound,evaluate
from gto.native.ev_audit import rank_five

class Precision(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.fast=fast_load(os.environ['GTO_PRECISION_LIBRARY']);cls.old=load(os.environ['GTO_ABSTRACT_LIBRARY'])
 def test_fast_rank_against_preserved_oracle_and_all_hand_categories(self):
  rng=random.Random(77119)
  fixed=[[32,36,40,44,48,0,5],[48,0,4,8,12,20,25],[48,49,50,51,44,40,36],[48,49,50,44,45,0,5],[48,49,44,45,40,41,0]]
  for cs in fixed+[rng.sample(range(52),7) for _ in range(20000)]:self.assertEqual(self.fast.precision_rank7(ints(cs)),rank(self.old,cs))
 def test_all990_conditional_runouts_match_independent_original_rank(self):
  for h,f in (([48,49,44,45],[0,17,30]),([48,44,1,5],[8,12,16]),([0,4,48,49],[8,12,16])):
   deck=[c for c in range(52) if c not in h+f];counts=[0,0,0]
   for turn,river in itertools.combinations(deck,2):
    a=rank(self.old,h[:2]+f+[turn,river]);b=rank(self.old,h[2:]+f+[turn,river]);counts[0 if a>b else 1 if a==b else 2]+=1
   self.assertEqual(exact(self.fast,h,f),tuple(counts));self.assertEqual(sum(counts),990)
 def test_full_allin_count_and_suit_isomorphism(self):
  h=[48,49,44,45];out=exact(self.fast,h)
  self.assertEqual(sum(out),1712304)
  self.assertEqual(out,(1410336,9308,292660))
  self.assertEqual(exact(self.fast,h[2:]+h[:2]),(out[2],out[1],out[0]))
  for permutation in itertools.permutations(range(4)):
   self.assertEqual(canonical(h),canonical(tuple(c//4*4+permutation[c%4] for c in h)))
  with self.assertRaises(ValueError):exact(self.fast,[0,0,1,2])
 def test_bound_keeps_shared_plane_covariance_and_exact_fold(self):
  a=bound(0,[[.2]*5],[[20.]*5],[[6400.]*5],256,.001)
  b=bound(0,[[1.,0,0,0,0]],[[20.,0,0,0,0]],[[6400.,0,0,0,0]],256,.001)
  self.assertAlmostEqual(a['radius_bb'],b['radius_bb'],places=12)
  f=bound(-9,[[0]*5],[[0]*5],[[0]*5],256,.001)
  self.assertEqual(f['interval_bb'],[-9,-9]);self.assertEqual(f['radius_bb'],0)
  with self.assertRaises(ValueError):bound(0,[[-1]*5],[[0]*5],[[0]*5],256,.01)
 def test_private_history_likelihood_and_branch_enumeration(self):
  # Opponent's raise likelihood differs by its private type, so posterior is3:1.
  nodes=[{'actor':1,'actions':['fold','raise'],'children':[1,2]},
   {'actor':-1,'value':1,'matched':False,'actions':[],'children':[]},
   {'actor':0,'actions':['fold','call'],'children':[3,4]},
   {'actor':-1,'value':-5,'matched':False,'actions':[],'children':[]},
   {'actor':-1,'value':5,'matched':True,'actions':[],'children':[]}]
  policy=[0.]*(5*3*2);policy[0:2]=[.25,.75];policy[2:4]=[.75,.25]
  policy[12:14]=[.5,.5];policy[14:16]=[.5,.5]
  constant,coef,denom=integrate_action(nodes,policy,[.25]*4,2,2,0,1,mode='checkdown')
  self.assertEqual(constant,0);self.assertEqual(denom,.25)
  self.assertAlmostEqual(coef[0][0],.75*.05);self.assertAlmostEqual(coef[1][0],.25*.05)
  folded,zero,_=integrate_action(nodes,policy,[.25]*4,2,2,0,0,mode='checkdown')
  self.assertEqual(folded,-2.5);self.assertEqual(sum(map(sum,zero)),0)
 def test_frozen_archive_identity_and_corruption_rejected(self):
  packet=json.loads(Path('docs/qa/ev-precision-20261030/frozen-inputs.json').read_text());k,p=unpack(packet)
  self.assertEqual(k['seed'],700017);self.assertEqual(set(p),{'checkdown','flop_controller'})
  self.assertEqual(len(k['mean']),5*169*169)
  packet['kernel_bytes_sha256']='0'*64
  with self.assertRaises(ValueError):unpack(packet)

 def test_rb_kernel_matches_independent_conditional_legacy_values(self):
  import subprocess
  from gto.abstract.model import ROOT,DP
  from gto.abstract.precision_runouts import BYTEP
  n=169;size=5*n*n;selected=((0,1),(0,14),(1,1),(14,14),(50,100));groups=classes();offset=[0];cards=[]
  for g in groups:cards.extend(c for pair in g for c in pair);offset.append(offset[-1]+len(g))
  mask=[1]*size
  for i,j in selected:
   for plane in range(5):mask[plane*n*n+i*n+j]=mask[plane*n*n+j*n+i]=0
  mean=(C.c_double*size)();variance=(C.c_double*size)();zero=(C.c_double*size)()
  self.assertEqual(self.fast.precision_kernel(n,ints(offset),ints(cards),2,901,(C.c_uint8*size)(*mask),zero,mean,variance),0)
  with tempfile.TemporaryDirectory() as d:
   source=Path(d)/'trace.cc';source.write_text('#include "'+str(ROOT/'gto/abstract/precision_native.cc')+'"\n'+
    'extern "C" void trace(int ti,int tj,const int*offset,const int*cards,int*out){std::mt19937 rng(901);for(int i=0;i<169;++i)for(int j=i;j<169;++j){std::vector<std::array<int,4>>deals;for(int a=offset[i];a<offset[i+1];++a)for(int b=offset[j];b<offset[j+1];++b){int x=cards[2*a],y=cards[2*a+1],z=cards[2*b],w=cards[2*b+1];if(x!=z&&x!=w&&y!=z&&y!=w)deals.push_back({x,y,z,w});}for(int s=0;s<2;++s){auto h=deals[std::uniform_int_distribution<size_t>(0,deals.size()-1)(rng)];std::vector<int>deck;for(int c=0;c<52;++c)if(std::find(h.begin(),h.end(),c)==h.end())deck.push_back(c);for(int k=0;k<5;++k){int q=std::uniform_int_distribution<int>(k,47)(rng);std::swap(deck[k],deck[q]);}if(i==ti&&j==tj){for(int k=0;k<4;++k)out[s*7+k]=h[k];for(int k=0;k<3;++k)out[s*7+4+k]=deck[k];}}if(i==ti&&j==tj)return;}}')
   target=Path(d)/'trace.so';subprocess.run(['c++','-std=c++17','-O2','-shared','-fPIC',str(source),'-o',str(target)],check=True)
   trace=C.CDLL(str(target));trace.trace.argtypes=[C.c_int,C.c_int,IP,IP,IP]
   for i,j in selected:
    worlds=(C.c_int*14)();trace.trace(i,j,ints(offset),ints(cards),worlds);values=[]
    for sample in range(2):
     h=list(worlds[sample*7:sample*7+4]);f=list(worlds[sample*7+4:sample*7+7]);deck=[c for c in range(52) if c not in h+f];total=0
     for tr in itertools.combinations(deck,2):
      a=rank(self.old,h[:2]+f+list(tr));b=rank(self.old,h[2:]+f+list(tr));total+=(a>b)-(a<b)
     equity=total/990
     def strong(hole):
      cs=hole+f;return rank_five(cs)[0]>=1 or max(sum(c%4==x for c in cs) for x in range(4))>=4
     oriented=[]
     for a,b,sign in ((h[:2],h[2:],1),(h[2:],h[:2],-1)):
      bb=strong(b);sb=strong(a);probe=sb or min(c//4 for c in a)>max(c//4 for c in f);row=[100*sign*equity]
      for x in (2,5,18,42):row.append(-x if bb and not sb else x if not bb and probe and not strong(b) else sign*equity*(x+(min(x,100-x) if bb or probe else 0)))
      oriented.append(row)
     if i==j:oriented=[[sum(x)/2 for x in zip(*oriented)]]*2
     values.append(oriented)
    for orientation,(row,col) in enumerate(((i,j),(j,i))):
     for plane in range(5):
      a,b=(v[orientation][plane] for v in values);idx=plane*n*n+row*n+col
      self.assertAlmostEqual(mean[idx],(a+b)/2,places=10)
      self.assertAlmostEqual(variance[idx],((a-(a+b)/2)**2+(b-(a+b)/2)**2),places=8)
 def test_all169_action_aggregates_match_independent_native_cf_evaluation(self):
  from gto.abstract.model import doubles,payoffs
  from gto.hand169 import CLASSES
  packet=json.loads(Path('docs/qa/ev-precision-20261030/frozen-inputs.json').read_text());k,policies=unpack(packet);nodes=tree();n=169;m=len(nodes);_,prob=chance(classes())
  for mode,policy in policies.items():
   values=(C.c_double*(m*3*n))();reach=(C.c_double*(m*n))();metrics=(C.c_double*4)()
   self.old.abstract_evaluate(n,m,ints([x['actor'] for x in nodes]),ints([len(x['actions']) for x in nodes]),ints([c for x in nodes for c in (x['children']+[-1]*3)[:3]]),doubles(prob),doubles(payoffs(k,mode,nodes)),doubles(policy),values,reach,metrics)
   report=evaluate(policy,k,mode)
   for v,node in enumerate(nodes):
    if node['actor']<0 or 'call' in node['history'] or node['raises']>=4:continue
    stage=('rfi','vs_open','vs_3bet','vs_4bet')[node['raises']]
    for h,label in enumerate(CLASSES):
     for a in range(len(node['actions'])):self.assertAlmostEqual(report['contexts'][stage]['hands'][label]['actions'][a]['ev_bb'],values[(v*3+a)*n+h]/2,places=10)
 def test_global_information_set_response_matches_independent_native(self):
  from gto.abstract.precision_game_bounds import evaluate as response
  from gto.abstract.model import doubles,payoffs
  nodes=tree();n=2;m=len(nodes);rng=random.Random(219);policy=[0.]*(m*3*n)
  for v,node in enumerate(nodes):
   if node['actor']<0:continue
   for h in range(n):
    raw=[rng.random()+.1 for _ in node['actions']]
    for a,x in enumerate(raw):policy[(v*3+a)*n+h]=x/sum(raw)
  p=[.4,.1,.1,.4];k={'mean':[],'variance':[0.]*20,'exact_mask':[True]*20,'samples_per_class_pair':256}
  for cap in (100,4,10,36,84):k['mean'].extend([0.,cap*.3,-cap*.3,0.])
  for mode in ('checkdown','flop_controller'):
   result=response(policy,k,mode,nodes=nodes,probability=p,n=n)
   leaf=[]
   for node in nodes:
    if node['actor']>=0:leaf.extend([0.]*4)
    elif not node['matched']:leaf.extend([float(node['value'])]*4)
    else:
     x=node['value'];plane=0 if mode=='checkdown' or x==100 else (2,5,18,42).index(x)+1
     leaf.extend(v*(x/100 if plane==0 else 1.) for v in k['mean'][plane*4:(plane+1)*4])
   ev=(C.c_double*(m*3*n))();reach=(C.c_double*(m*n))();metrics=(C.c_double*4)()
   self.old.abstract_evaluate(n,m,ints([x['actor'] for x in nodes]),ints([len(x['actions']) for x in nodes]),ints([c for x in nodes for c in (x['children']+[-1]*3)[:3]]),doubles(p),doubles(leaf),doubles(policy),ev,reach,metrics)
   self.assertAlmostEqual(result['nashconv_point_bb'],metrics[3]/2,places=11)
   self.assertAlmostEqual(result['players'][0]['profile_ev_bb'],metrics[0]/2,places=11)
   self.assertAlmostEqual(sum(x['profile_ev_bb'] for x in result['players']),0,places=11)
   self.assertLessEqual(result['nashconv_interval_bb'][0],metrics[3]/2)
   self.assertGreaterEqual(result['nashconv_interval_bb'][1],metrics[3]/2)
   self.assertFalse(result['real_game_gto_verified'])

if __name__=='__main__':unittest.main()
