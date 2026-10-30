"""Exact targeted all-in cells and flop-conditioned full turn/river integration."""
import ctypes as C,hashlib,json,math,subprocess,time
from collections import Counter
from fractions import Fraction
from itertools import permutations
from pathlib import Path
from gto.abstract.model import classes,ints,IP,DP
from gto.hand169 import CLASSES

BYTEP=C.POINTER(C.c_uint8);UP=C.POINTER(C.c_uint64)

def build(output):
 output=Path(output);output.mkdir(parents=True,exist_ok=True);source=Path(__file__).with_name('precision_native.cc');lib=output/'precision.so'
 flags=['-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC']
 subprocess.run(['c++',*flags,str(source),'-o',str(lib)],check=True)
 (output/'precision-manifest.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'flags':flags,'compiler':subprocess.check_output(['c++','--version'],text=True).splitlines()[0]},sort_keys=True)+'\n')
 return load(lib)

def load(path):
 lib=C.CDLL(str(Path(path).resolve()));lib.precision_rank7.argtypes=[IP];lib.precision_rank7.restype=C.c_uint64
 lib.precision_exact.argtypes=[IP,IP,C.c_int,UP];lib.precision_exact.restype=C.c_int
 lib.precision_kernel.argtypes=[C.c_int,IP,IP,C.c_int,C.c_int,BYTEP,DP,DP,DP];lib.precision_kernel.restype=C.c_int
 return lib

def exact(lib,holes,flop=()):
 if len(holes)!=4 or len(flop) not in (0,3) or len(set([*holes,*flop]))!=4+len(flop) or any(type(x) is not int or not 0<=x<52 for x in (*holes,*flop)):raise ValueError('four distinct holes/zero or three public flop cards')
 out=(C.c_uint64*3)()
 if lib.precision_exact(ints(holes),ints(flop),len(flop),out):raise ValueError('conditional enumeration failed')
 if sum(out)!=(990 if flop else math.comb(48,5)):raise ValueError('runout count differs')
 return tuple(out)

SUITS=tuple(permutations(range(4)))
def canonical(holes):
 return min(tuple(sorted(c//4*4+p[c%4] for c in holes[:2]))+tuple(sorted(c//4*4+p[c%4] for c in holes[2:])) for p in SUITS)

def exact_cells(lib,*,opponent_classes=('AA','KK'),prior=None):
 """Fixed predeclared targets: every pocket-pair match, AA/KK versus all types.

 Identical class showdown expectation is exactly zero by seat-exchange symmetry.
 Pocket-pair opponents always satisfy both fixed flop call/lead predicates, so
 non-all-in controller payoffs are analytically scaled showdown values as well.
 """
 n=169;size=n*n;groups=classes();mask=list(prior['mask']) if prior else [0]*(5*size);values=list(prior['values']) if prior else [0.]*(5*size);records=list(prior['records']) if prior else [];known={tuple(r['classes']) for r in records};cache={};start=time.monotonic()
 for i,a in enumerate(CLASSES):
  for j in range(i,n):
   b=CLASSES[j]
   if (a,b) in known:continue
   pocket=len(a)==len(b)==2
   if i!=j and not pocket and a not in opponent_classes and b not in opponent_classes:continue
   if i==j:mean=Fraction(0);count=sum(not set(x)&set(y) for x in groups[i] for y in groups[j]);numerator=0;denominator=count*math.comb(48,5)
   else:
    variants=Counter(canonical(x+y) for x in groups[i] for y in groups[j] if not set(x)&set(y));count=sum(variants.values());numerator=0;denominator=count*math.comb(48,5)
    for hole,multiplicity in variants.items():
     if hole not in cache:cache[hole]=exact(lib,hole)
     win,tie,loss=cache[hole];numerator+=multiplicity*(win-loss)
    mean=Fraction(100*numerator,denominator)
   for plane,x in enumerate((100,2,5,18,42)):
    if plane and not pocket:continue
    factor=Fraction(1) if plane==0 else Fraction(x+min(x,100-x),100)
    for row,col,sign in ((i,j,1),(j,i,-1)):
     if row==col:sign=1
     pos=plane*size+row*n+col;mask[pos]=1;values[pos]=float(sign*mean*factor)
   records.append({'classes':[a,b],'compatible_hole_assignments':count,'signed_wins_numerator':numerator,'board_weight_denominator':denominator,'mean_chips_fraction':[mean.numerator,mean.denominator],'pocket_pair_closed_form':pocket})
 return {'mask':mask,'values':values,'records':records,'concrete_matchups_enumerated':len(cache)+(prior['concrete_matchups_enumerated'] if prior else 0),'boards_per_matchup':math.comb(48,5),'seconds':time.monotonic()-start+(prior['seconds'] if prior else 0),'targets':list(opponent_classes)}

def rao_blackwell(lib,exact_result,*,samples=256,seed=700017):
 n=169;size=5*n*n;offset=[0];cards=[]
 for g in classes():cards.extend(c for pair in g for c in pair);offset.append(offset[-1]+len(g))
 means=(C.c_double*size)();variance=(C.c_double*size)();start=time.monotonic()
 if lib.precision_kernel(n,ints(offset),ints(cards),samples,seed,(C.c_uint8*size)(*exact_result['mask']),(C.c_double*size)(*exact_result['values']),means,variance):raise ValueError('conditional kernel failed')
 return {'seed':seed,'samples_per_class_pair':samples,'mean':list(means),'variance':list(variance),'exact_mask':exact_result['mask'],
  'integration':'all990 turn/river boards per sampled compatible hole/flop; exact targeted all-in/pocket-pair closures',
  'seconds':time.monotonic()-start,'full_game_accuracy_verified':False}


def allocation_targets(policies):
 """Choose two non-pair classes from frozen vs4bet reach; no validation values."""
 from gto.abstract.model import tree,chance
 nodes=tree();_,p=chance(classes());n=169;totals=[0.]*n
 for policy in policies.values():
  def visit(v,r0,r1):
   node=nodes[v]
   if node['actor']<0:return
   if node['raises']==3 and 'call' not in node['history']:
    scores=[sum(p[i*n+j]*r0[i]*r1[j] for j in range(n)) for i in range(n)];z=sum(scores)
    for i,x in enumerate(scores):totals[i]+=x/z
    return
   for a,child in enumerate(node['children']):
    r=[x*policy[(v*3+a)*n+h] for h,x in enumerate(r0 if node['actor']==0 else r1)]
    visit(child,r if node['actor']==0 else r0,r1 if node['actor']==0 else r)
  visit(0,[1.]*n,[1.]*n)
 selected=sorted((i for i,label in enumerate(CLASSES) if len(label)!=2),key=lambda i:(-totals[i],CLASSES[i]))[:2]
 return ('AA','KK',*(CLASSES[i] for i in selected))
