import ctypes as C,json,math,tempfile,unittest
from pathlib import Path
from gto.abstract import fullsupport as fs,independent_preflop as study,independent_evaluation as ev,model,root_interval as ri,street_tree as st
from gto.abstract.model import doubles,ints

class IndependentPreflopTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.native=fs.build(Path(cls.tmp.name)/'oracle');cls.coeff=ri.build(Path(cls.tmp.name)/'coeff')
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_numeric_packets_reject_checksum_corruption(self):
  p=fs.pack([0.,-1.,.5,50.]);self.assertEqual(fs.unpack(p),[0.,-1.,.5,50.]);p['sha256']='0'*64
  with self.assertRaises(ValueError):fs.unpack(p)
 def test_class_board_likelihood_and_exact_allin_equity(self):
  # Independent four-card fixture: two legal ordered pairs, four incompatible pairs.
  n=3;cards=ints([0,1,2,3,0,2]);labels=ints([0,1,2]);groups=ints([0,0,0]);wins=(C.c_uint16*9)(0,990,0,0,0,0,0,0,0);ties=(C.c_uint16*9)();full=ints([2]*fs.S);out=(C.c_double*fs.S)();mass=(C.c_double*fs.S)()
  self.assertEqual(self.native.fullsupport(n,1,cards,labels,groups,wins,ties,doubles([-50.]*64),doubles([100.]*64),full,out,mass),0)
  self.assertAlmostEqual(mass[1],1/(2*17296));self.assertAlmostEqual(out[1],50/(2*17296));self.assertAlmostEqual(out[169],-50/(2*17296));self.assertEqual(mass[2],0.)
 def test_importance_control_variate_preserves_full_population_expectation(self):
  mean=(C.c_double*fs.S)();m2=(C.c_double*fs.S)();control=doubles([2.]*fs.S)
  # Two physical-board populations, with normalized conditional mass (uniform Q).
  for i,(u,w) in enumerate(((5.,.5),(-1.,1.5))):
   self.native.oracle_update(1,i+1,doubles([u*w/22100]*fs.S),doubles([w/22100]*fs.S),control,mean,m2)
  self.assertAlmostEqual(mean[0],.5);self.assertAlmostEqual(m2[0],18.)
 def test_whole_policy_keeps_correlated_observations(self):
  mean=(C.c_double*1)();m2=(C.c_double*1)();weights=[0.]*fs.S;weights[:2]=[.5,.5];zero=doubles([0.]*fs.S);mass=zero
  for i,v in enumerate((2.,-2.)):
   y=[0.]*fs.S;y[:2]=[v/22100,v/22100];self.native.scalar_update(1,1,i+1,doubles(y),mass,zero,doubles(weights),doubles([1.]),mean,m2)
  self.assertAlmostEqual(mean[0],1.);self.assertAlmostEqual(m2[0],8.) # not half the actual variance
 def test_interval_includes_support_and_rejects_invalid_inputs(self):
  lo,hi,r=fs.empirical_interval(2.,1.,512,5.,2.,.001);self.assertLessEqual(lo,2.);self.assertGreaterEqual(hi,2.);self.assertGreater(r,0.)
  with self.assertRaises(ValueError):fs.empirical_interval(0.,0.,1,5.,0.,.01)
  with self.assertRaises(ValueError):fs.empirical_interval(0.,0.,5,5.,6.,.01)
 def test_perfect_information_opponent_is_not_an_observation(self):
  import inspect
  from gto.abstract.flop_conditional import Observation
  self.assertNotIn('opponent',inspect.signature(Observation).parameters)
  m={'pairs':[(0,5),(48,49)],'flop':[12,17,22]};self.assertEqual(fs.groups(m),fs.groups({**m,'opponent_cards':[40,41]}))
 def test_seat_swapped_affine_payoff_cash_identity(self):
  r={'post_call_pot_bb':18.,'remaining_stack_bb':41.,'hero_actor':1};g=fs.game(r,[.5,1.,2.],[1/64]*64,[.5/64]*64);a,b=ri.coefficients(self.coeff,g,st.uniform(g));teacher={'ranges':[{**r,'leaf_index':9}],'profiles':{'one':{'9|paired':st.uniform(g)}}};aa,bb,_,_=fs.coefficients(teacher,{'variants':{'one':[.5,1.,2.]}},'paired',self.coeff)
  for i in range(8):
   for j in range(8):
    for e in (0.,.3,1.):self.assertAlmostEqual(aa[i*8+j]+bb[i*8+j]*e,-(a[j*8+i]+b[j*8+i]*(1-e)),places=12)
 def test_every_terminal_has_a_real_payoff_plane(self):
  names=[('one',i) for i,n in enumerate(model.tree()) if n['actor']<0 and n['matched']];data=[3.]*(len(names)*fs.S);o={k:fs.pack(data) for k in ('point','lower','upper')};values=fs.payoff_planes(o,{},'one',names)['point']
  for i,node in enumerate(model.tree()):
   if node['actor']<0:self.assertEqual(values[i*fs.S],6. if node['matched'] else node['value'])
  with self.assertRaises(ValueError):fs.payoff_planes(o,{},'missing',names)
 def test_real_flop_class_payoffs_match_private_type_game_for_both_seats(self):
  from gto.abstract import call_study as cs,gap_models as gm
  from gto.abstract.factorial_transfer import category
  env=cs.setup(Path(self.tmp.name)/'actual');flop=[8,13,18];m=cs.exact.matrix(env[0],flop);groups=fs.groups(m);ranges=[__import__('gto.abstract.call_reach',fromlist=['extract']).extract(env[3],h,'test') for h in (['raise_to_5','call'],['raise_to_5','raise_to_18','call'])];profiles={};games=[]
  for r in ranges:
   moments=(C.c_double*128)();self.assertEqual(env[1].type_aggregate(m['n'],8,8,m['cards'],ints(m['labels']),ints(groups),ints(groups),m['win'],m['tie'],doubles(r['hero_reach']),doubles(r['villain_reach']),moments),0)
   g=fs.game(r,[.5,1.,2.],list(moments)[::2],list(moments)[1::2]);pi=st.uniform(g);profiles[str(r['leaf_index'])+'|'+category(flop)]=pi;games.append((g,pi))
  coef=fs.coefficients({'ranges':ranges,'profiles':{'one':profiles}},{'variants':{'one':[.5,1.,2.]}},category(flop),self.coeff);y,mass=fs.evaluate_flop(self.native,env[0],flop,coef);full=ri.full_counts()
  for plane,(r,(g,pi)) in enumerate(zip(ranges,games)):
   z=gm.direct_mass(env[5],r,flop);observed=math.fsum(y[plane*fs.S+i*169+j]*full[i*169+j]*17296*r['seat_reach'][0][i]*r['seat_reach'][1][j] for i in range(169) for j in range(169))/z;expected=st.evaluate(env[-1],g,pi)['profile_hero_ev_bb']*(1 if r['hero_actor']==0 else -1);self.assertAlmostEqual(observed,expected,places=11)
  self.assertTrue(all(0<=x<=1/17296 for x in mass))
 def test_replay_compares_decoded_values_and_checks_each_packet(self):
  from gto.abstract.independent_verify import compare
  p=fs.pack([1.,2.]);compare(p,fs.pack([1.+1e-13,2.]));compare(p,{k:v for k,v in p.items() if k!='data'});q={**p,'sha256':'bad'}
  with self.assertRaises(ValueError):compare(p,q)
 def test_policy_mixing_is_seat_local_and_nonmutating(self):
  n=len(model.tree())*3*169;a=[1.]*n;b=[2.]*n;c=ev.mix(a,b)
  for k,node in enumerate(model.tree()):self.assertEqual(c[k*3*169],2. if node['actor']==1 else 1.)
  self.assertEqual(a,[1.]*n)
 def test_design_fixed_before_payoff_and_independent_seeds(self):
  p=json.loads(study.P.read_text());d=study.design(p);self.assertTrue(d['no_payoff_seen']);self.assertFalse(d['selection_performed']);self.assertEqual(d,study.design(p));self.assertEqual(len(d['teacher']),32);self.assertEqual({k:len(v) for k,v in d['draws'].items()},{'pilot':16,'train':256,'evaluation':512})
  self.assertEqual(len({p['oracle'][k]['seed'] for k in d['draws']}),3)
 def test_preflop_leaf_weights_conserve_root_probability(self):
  nodes=model.tree();pi=[0.]*(len(nodes)*3*169)
  for k,n in enumerate(nodes):
   for a in range(len(n['actions'])):pi[(k*3+a)*169:(k*3+a+1)*169]=[1/len(n['actions'])]*169
  weights,fold=ev.weights(pi,[]);ledger=__import__('gto.abstract.call_reach',fromlist=['leaf_ledger']).leaf_ledger(pi)
  self.assertEqual(len(weights),9);self.assertAlmostEqual(sum(map(math.fsum,weights.values())),sum(x['probability'] for x in ledger if x['matched']),places=12);self.assertAlmostEqual(fold,sum(x['probability']*x['fold_sb_payoff_bb'] for x in ledger if not x['matched']))

if __name__=='__main__':unittest.main()
