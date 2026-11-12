"""Public-history reached-opponent features; no actual opponent card input."""
import ctypes as C,hashlib,json,math,subprocess
from pathlib import Path
from gto.abstract.model import ints,doubles,IP,DP
from gto.hand169 import CLASSES
from gto.abstract.flop_exact import U16
from gto.abstract.frozen_flop_reach import frozen_reach
from gto.abstract.generalization_features import uniform_strength,signal as uniform_signal,distance_parts
from gto.abstract.continuation_learning import FrozenContinuation

def build(directory):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);src=Path(__file__).with_name('reached_range.cc');target=directory/'reached-range.so';subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(src),'-o',str(target)],check=True);lib=C.CDLL(str(target.resolve()));lib.reached_features.argtypes=[C.c_int,IP,IP,U16,U16,DP,DP];lib.reached_features.restype=C.c_int;return lib

def conditional(lib,m,opponent_reach):
 if len(opponent_reach)!=169:raise ValueError('complete public class-reach vector required')
 out=(C.c_double*(m['n']*6))()
 if lib.reached_features(m['n'],m['cards'],ints(m['labels']),m['win'],m['tie'],doubles(opponent_reach),out):raise ValueError('invalid reached range or cards')
 return {tuple(sorted(p)):{'mass':out[i*6],'equity':out[i*6+1] if out[i*6]>0 else None,'win':out[i*6+2] if out[i*6]>0 else None,'tie':out[i*6+3] if out[i*6]>0 else None,'ahead_probability':out[i*6+4] if out[i*6]>0 else None,'opponent_equity_std':out[i*6+5] if out[i*6]>0 else None} for i,p in enumerate(m['pairs'])}

def books(lib,m,pi,stage,uniform=None):
 uniform=uniform if uniform is not None else uniform_strength(m)
 r=frozen_reach(stage,pi,after_call=True);opponents={r['hero_actor']:r['villain_reach'],1-r['hero_actor']:r['hero_reach']};data={actor:conditional(lib,m,v) for actor,v in opponents.items()};audits=[]
 for actor,rows in data.items():
  valid=[v for v in rows.values() if v['equity'] is not None];examples=[]
  for label in ('AA','AKs','72o'):
   own=next((tuple(sorted(p)) for p,c in zip(m['pairs'],m['labels']) if c==CLASSES.index(label)),None)
   if own is not None:examples.append({'own_class':label,'own_cards':list(own),'uniform_equity':uniform[own],**rows[own]})
  audits.append({'actor':actor,'own_hand_examples':examples,'opponent_reach_sha256':hashlib.sha256(json.dumps(opponents[actor],separators=(',',':')).encode()).hexdigest(),'valid_own_pairs':len(valid),'zero_opponent_mass_pairs':len(rows)-len(valid),'equity_min':min(v['equity'] for v in valid),'equity_max':max(v['equity'] for v in valid),'normalization_mass_min':min(v['mass'] for v in valid),'normalization_mass_max':max(v['mass'] for v in valid)})
 return {'uniform':uniform,'by_actor':data,'public_history':r['history']+['call'],'stage':stage,'hero_actor':r['hero_actor'],'audits':audits,'basis':'opposite-seat frozen prefix+CALL class reach; remove own+public cards,normalize; own reach cancels GIVEN own cards','std_is_sampling_error':False,'actual_opponent_cards_required':False}

def signal(obs,book):
 old=uniform_signal(obs,book['uniform']);row=book['by_actor'][obs.actor][tuple(sorted(obs.holes))];valid=row['equity'] is not None
 return (*old,min(15,int(row['equity']*16)) if valid else 0,min(3,int(row['ahead_probability']*4)) if valid else 0,int(valid))

class Neighbors:
 """Share geometry across initial seeds,never share learned probabilities."""
 def __init__(self,configs):self.configs=configs;self.cache={};self.catalog={}
 def get(self,records,k):
  rid=id(records)
  if rid not in self.catalog:self.catalog[rid]=(hashlib.sha256(json.dumps([r['key'] for r in records],separators=(',',':')).encode()).hexdigest(),records)
  digest=self.catalog[rid][0];ck=(digest,k)
  if ck in self.cache:return self.cache[ck]
  components=[]
  for i,row in enumerate(records):
   q=tuple(row['key'])
   if k[:3]!=q[:3]:continue
   private,pub=distance_parts(k,q);rg=((k[20]-q[20])/15)**2+.5*((k[21]-q[21])/3)**2;components.append((i,private,pub,rg,q[20],q[22]))
  result={}
  for cfg in self.configs:
   scored=[(p*cfg['private_weight']+b*cfg['board_weight']+r*cfg['range_weight'],i,eq) for i,p,b,r,eq,valid in components if cfg['family']=='uniform' or valid==k[22]]
   if cfg['method']=='hardbin':
    restricted=[x for x in scored if abs(x[2]-k[20])<=1];scored=restricted or scored
   top=sorted(scored)[:cfg['neighbors']]
   if not top:result[cfg['name']]=[];continue
   md=top[0][0];weights=[math.exp(-(d-md)/cfg['bandwidth']) if cfg['method']=='kernel' else 1/(d+1e-6) for d,_,_ in top];z=math.fsum(weights);result[cfg['name']]=[(idx,w/z) for w,(_,idx,_) in zip(weights,top)]
  self.cache[ck]=result;return result

class RangePolicy:
 def __init__(self,records,config,geometry):self.records=records;self.config=config;self.geometry=geometry;self.cache={}
 def probabilities(self,k):
  if k not in self.cache:
   neighbors=self.geometry.get(self.records,k)[self.config['name']];p=tuple(math.fsum(w*self.records[i]['probabilities'][a] for i,w in neighbors) for a in range(4)) if neighbors else (.25,)*4;z=math.fsum(p);self.cache[k]=tuple(v/z for v in p)
  return self.cache[k]
 def materialize(self,g):return FrozenContinuation({k:self.probabilities(k) for k in g['hkeys']+g['vkeys']})
