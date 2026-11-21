import ctypes as C,itertools,json,math,tempfile,unittest
from pathlib import Path
from gto.abstract import suit_exact as s,fullsupport as fs,model
from gto.abstract.suit_exact_br import evaluate
from gto.abstract.model import doubles
class SuitExactTests(unittest.TestCase):
 def test_complete_orbits_and_representatives_do_not_depend_on_values(self):
  d=s.design();self.assertEqual(len(d['orbits']),1755);self.assertEqual(sum(r['multiplicity'] for r in d['orbits']),22100);self.assertFalse(d['selection_uses_payoffs']);self.assertFalse(d['new_unseen_test']);self.assertTrue(all(s.canonical(r['representative'])==tuple(r['canonical']) for r in d['orbits']))
 def test_global_permutation_preserves_class_and_public_category(self):
  from gto.abstract.factorial_transfer import category
  for b in ([0,1,2],[0,1,4],[0,4,8],[0,5,10],[40,41,20]):
   for p in s.PERM:
    q=[x//4*4+p[x%4] for x in b];self.assertEqual(s.canonical(q),s.canonical(b));self.assertEqual(category(q),category(b))
 def test_exact_accumulator_uses_multiplicity_not_uniform_orbit_weight(self):
  with tempfile.TemporaryDirectory() as t:
   lib=s.build(Path(t));out=(C.c_longdouble*fs.S)();mass=(C.c_longdouble*fs.S)();self.assertEqual(lib.accumulate(1,12,doubles([.1]*fs.S),doubles([.01]*fs.S),out,mass),0);self.assertEqual(lib.accumulate(1,4,doubles([.2]*fs.S),doubles([.02]*fs.S),out,mass),0);self.assertAlmostEqual(out[0],2.);self.assertAlmostEqual(mass[0],.2)
 def test_independent_br_has_no_opponent_card_maximization(self):
  nodes=[{'actor':0,'actions':['a','b'],'children':[1,2]},{'actor':-1},{'actor':-1}];pi=[0.]*18;pi[:2]=[.5,.5];pi[2:4]=[.5,.5];chance=[.25]*4;leaf=[0.]*4+[2.,-2.,-2.,2.]+[-2.,2.,2.,-2.];r=evaluate(nodes,pi,chance,leaf,2);self.assertEqual(r['br_sb_ev_bb'],0.);self.assertEqual(r['abstract_nashconv_bb'],0.)
 def test_independent_br_matches_enumerated_pure_policy_responses(self):
  nodes=[{'actor':0,'actions':['a','b'],'children':[1,4]},{'actor':1,'actions':['a','b'],'children':[2,3]},{'actor':-1},{'actor':-1},{'actor':1,'actions':['a','b'],'children':[5,6]},{'actor':-1},{'actor':-1}];pi=[0.]*(7*3*2)
  for k in (0,1,4):
   for a in range(2):pi[(k*3+a)*2:(k*3+a+1)*2]=[.3 if a==0 else .7]*2
  leaf=[float((i*7)%19-9) for i in range(28)];prob=[.4,.1,.2,.3];r=evaluate(nodes,pi,prob,leaf,2)
  def value(k,i,j,p):
   n=nodes[k]
   if n['actor']<0:return leaf[k*4+i*2+j]
   return sum(p[(k*3+a)*2+(i if n['actor']==0 else j)]*value(c,i,j,p) for a,c in enumerate(n['children']))
  for seat in (0,1):
   rows=[(k,h) for k,n in enumerate(nodes) if n['actor']==seat for h in range(2)];scores=[]
   for choices in itertools.product(range(2),repeat=len(rows)):
    p=list(pi)
    for (k,h),a in zip(rows,choices):p[(k*3)*2+h]=float(a==0);p[(k*3+1)*2+h]=float(a==1)
    scores.append(sum(prob[i*2+j]*value(0,i,j,p)/2 for i in range(2) for j in range(2)))
   self.assertAlmostEqual(r['br_sb_ev_bb' if seat==0 else 'br_bb_min_sb_ev_bb'],max(scores) if seat==0 else min(scores),places=12)

if __name__=='__main__':unittest.main()
