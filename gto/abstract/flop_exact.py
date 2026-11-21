"""Rank-cache exact integration of every compatible hole pair on a fixed flop."""
import ctypes as C,hashlib,json,math,subprocess,time
from pathlib import Path
from gto.abstract.flop_conditional import legal_groups,validate_flop
from gto.abstract.frozen_flop_reach import frozen_reach
from gto.abstract.model import ints,IP,DP,doubles
from gto.hand169 import CLASSES
U16=C.POINTER(C.c_uint16)

def build(directory):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);source=Path(__file__).with_name('flop_exact_matrix.cc');target=directory/'flop-exact.so'
 subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(source),'-o',str(target)],check=True)
 lib=C.CDLL(str(target.resolve()));lib.flop_matrix.argtypes=[C.c_int,IP,IP,U16,U16];lib.flop_matrix.restype=C.c_int
 lib.flop_expectation.argtypes=[C.c_int,IP,IP,IP,U16,U16,DP,DP,C.c_int,C.c_int,C.c_int,DP];lib.flop_expectation.restype=C.c_int
 return lib

def matrix(lib,flop,holes=None):
 validate_flop(flop);groups=legal_groups(flop)
 label_map={tuple(sorted(p)):h for h,g in enumerate(groups) for p in g}
 ordered=[(h,p) for h,g in enumerate(groups) for p in g] if holes is None else [(label_map.get(tuple(sorted(p)),-1),tuple(p)) for p in holes]
 pairs=[p for _,p in ordered];labels=[h for h,_ in ordered];n=len(pairs)
 if not n or len({tuple(sorted(p)) for p in pairs})!=n:raise ValueError('nonempty unique hole pairs required')
 for p in pairs:
  if len(p)!=2 or any(type(c) is not int or not 0<=c<52 for c in p) or len(set(p+tuple(flop)))!=5:raise ValueError('legal private cards required')
 w=(C.c_uint16*(n*n))();t=(C.c_uint16*(n*n))();cards=ints([c for p in pairs for c in p]);start=time.perf_counter()
 if lib.flop_matrix(n,cards,ints(flop),w,t):raise ValueError('exact hole matrix failed')
 return {'n':n,'pairs':pairs,'labels':labels,'cards':cards,'flop':tuple(flop),'win':w,'tie':t,'seconds':time.perf_counter()-start}

def evaluate(lib,m,policy,stage):
 if m['n']!=1176:raise ValueError('complete fixed-flop matrix required for frozen posterior')
 r=frozen_reach(stage,policy,after_call=True);out=(C.c_double*(169*5))()
 if lib.flop_expectation(m['n'],m['cards'],ints(m['labels']),ints(m['flop']),m['win'],m['tie'],doubles(r['hero_reach']),doubles(r['villain_reach']),r['hero_actor'],int(r['matched_contribution_bb']),int(r['remaining_stack_bb']),out):raise ValueError('conditional exact expectation failed')
 mass=math.fsum(out[h*5] for h in range(169));rows=[]
 if mass<=0:raise ValueError('zero posterior mass')
 for h,label in enumerate(CLASSES):
  z=out[h*5];row={'hand':label,'posterior_probability':z/mass,'equity':out[h*5+1]/z if z else None,'old_ev_bb':out[h*5+2]/z if z else None,'new_ev_bb':out[h*5+3]/z if z else None,'delta_bb':out[h*5+4]/z if z else None};rows.append(row)
 values={key:math.fsum(out[h*5+k] for h in range(169))/mass for k,key in ((2,'old'),(3,'new'),(4,'delta'))}
 return {'stage':stage,'flop':list(m['flop']),'rows':rows,'aggregate':values,'posterior_mass_unnormalized':mass,'hole_sampling_error_bb':0,'runout_sampling_error_bb':0,'numerical_guard_bb':1e-8,'numerical_guard_note':'extended-precision sums; conservative arithmetic guard, NOT a statistical interval','method':'all compatible hole assignments and all990 runouts; cached own-hand ranks and seat exchange','compatible_ordered_hole_pairs':1271256,'unique_unordered_pairs':635628,'full_game_gto_verified':False,'model_approximation_error_bb':None,'external_gto_deviation_bb':None}
