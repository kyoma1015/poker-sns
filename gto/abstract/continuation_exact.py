"""Exact controller values and an untuned check/call ablation, not a GTO reference."""
import ctypes as C,hashlib,json,math,subprocess,time
from collections import Counter
from fractions import Fraction
from pathlib import Path
from gto.abstract.model import tree,chance,classes,ints,IP
from gto.abstract.precision_runouts import canonical,refinement_targets
from gto.hand169 import CLASSES

LP=C.POINTER(C.c_int64)
def build(directory):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);source=Path(__file__).with_suffix('.cc');target=directory/'controller.so'
 subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(source),'-o',str(target)],check=True)
 return load(target)
def load(path):
 lib=C.CDLL(str(Path(path).resolve()));lib.precision_controller_exact.argtypes=[IP,LP];lib.precision_controller_exact.restype=C.c_int
 lib.precision_controller_board.argtypes=[IP,IP,LP];lib.precision_controller_board.restype=C.c_int
 return lib

def select_cells(policies):
 """Top20 suited calling types, equal model/history weight, frozen policy only."""
 nodes=tree();_,p=chance(classes());n=169;scores=[0.]*n
 for policy in policies.values():
  def walk(v,r0,r1):
   node=nodes[v]
   if node['actor']<0:return
   if node['raises'] in (2,3) and 'call' not in node['history']:
    actor=node['actor'];a=node['actions'].index('call')
    raw=[math.fsum(p[h*n+j]*r1[j] for j in range(n))*r0[h] if actor==0 else math.fsum(p[j*n+h]*r0[j] for j in range(n))*r1[h] for h in range(n)]
    raw=[x*policy[(v*3+a)*n+h] for h,x in enumerate(raw)];z=math.fsum(raw)
    if z:
     for h,x in enumerate(raw):scores[h]+=x/z
   for a,c in enumerate(node['children']):
    r=[x*policy[(v*3+a)*n+h] for h,x in enumerate(r0 if node['actor']==0 else r1)]
    walk(c,r if node['actor']==0 else r0,r1 if node['actor']==0 else r)
  walk(0,[1.]*n,[1.]*n)
 heroes=sorted((i for i,h in enumerate(CLASSES) if h.endswith('s')),key=lambda i:(-scores[i],CLASSES[i]))[:20]
 opponents=[CLASSES.index(h) for h in refinement_targets(policies)]
 return sorted(set(tuple(sorted((i,j))) for i in heroes for j in opponents))

def refine(exact,policies,lib):
 groups=classes();n=169;size=n*n;start=time.monotonic();out={**exact,'mask':list(exact['mask']),'values':list(exact['values'])};records=[];cache={}
 for i,j in select_cells(policies):
  variants=Counter(canonical(x+y) for x in groups[i] for y in groups[j] if not set(x)&set(y));denom=sum(variants.values())*math.comb(48,5)*10;totals=[0]*5
  for hole,multiplicity in variants.items():
   if hole not in cache:
    counts=(C.c_int64*5)()
    if lib.precision_controller_exact(ints(hole),counts):raise ValueError('exact controller holes invalid')
    cache[hole]=tuple(counts)
   for v,value in enumerate(cache[hole]):totals[v]+=multiplicity*value
  factors=[Fraction(x,denom) for x in totals[1:]]
  # Showdown enumeration must independently agree with the saved all-in cell.
  if not math.isclose(float(Fraction(1000*totals[0],denom)),exact['values'][i*n+j],abs_tol=1e-12):raise ValueError('controller enumeration showdown identity differs')
  for d,(row,col) in enumerate(((i,j),(j,i))):
   for plane,x in enumerate((2,5,18,42),1):
    idx=plane*size+row*n+col;out['mask'][idx]=1;out['values'][idx]=float(x*factors[d])
  records.append({'classes':[CLASSES[i],CLASSES[j]],'compatible_hole_assignments':sum(variants.values()),'partition_denominator':denom,'old_factors':[[v.numerator,v.denominator] for v in factors[:2]],'checkcall_ablation_factors':[[v.numerator,v.denominator] for v in factors[2:]],'ablation_is_accuracy_improvement':False})
 out['controller_records']=records;out['controller_concrete_matchups']=len(cache);out['controller_seconds']=time.monotonic()-start
 out['controller_method']='all C(48,5) boards and all10 flop partitions; rank once per board; original model retained; checkcall ablation not calibrated'
 return out
