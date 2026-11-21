import copy,json,math,os,random,unittest
from types import SimpleNamespace
from unittest.mock import patch
from gto.qualification.coverage_solver import CoverageSolver,chance_plan,family_prior,GROUPS,adaptive_probabilities
from gto.qualification import coverage_solver as module
from gto.qualification import blind_oracle as oracle

class ChanceAndBatch(unittest.TestCase):
    def test_true_card_law_and_no_replacement(self):
        self.assertEqual(sum(map(len,GROUPS)),1326)
        plan=chance_plan(random.Random(1811));seen=set()
        bycombo={tuple(sorted(h)):i for i,g in enumerate(GROUPS) for h in g}
        for deck,seeds,w in plan:
            self.assertEqual(len(set(deck)),9);self.assertEqual(len(seeds),2)
            k=bycombo[tuple(sorted(deck[:2]))];seen.add(k)
            # q(own combo)=1/169/size. w*q must be the true1/1326.
            self.assertAlmostEqual(w/(169*len(GROUPS[k])),1/1326,places=15)
            # Opponent conditional sample law is unchanged:1225 pairs remain.
            self.assertEqual(math.comb(52-len(deck[:2]),2),1225)
        self.assertEqual(len(seen),169)
    def test_action_prior_positive_and_family_not_size_count(self):
        for actions in ((0,1),(1,4,5),(0,1,4,5,6,102)):
            pi=family_prior(actions);self.assertAlmostEqual(sum(pi),1)
            self.assertTrue(all(p>0 for p in pi))
        p=family_prior((0,1,*range(4,103)))
        self.assertAlmostEqual(p[0],1/3);self.assertAlmostEqual(p[1],1/3);self.assertAlmostEqual(sum(p[2:]),1/3)
    def test_frozen_batch_chance_weight_matches_independent_CF_and_average(self):
        finite=oracle.FiniteCFR('exact');pi=oracle.policy(finite.rows)
        _,expectedg,expecteda=oracle.exact(pi)
        s=CoverageSolver(None,None);s.rows=copy.deepcopy(finite.rows);before=copy.deepcopy(s.rows)
        strata=[[w for w in oracle.WORLDS if w[0]//2==0],[w for w in oracle.WORLDS if w[0]//2!=0]]
        conditional=[]
        for worlds in strata:
            with patch.object(oracle,'WORLDS',tuple(worlds)):_,g,a=oracle.exact(pi)
            conditional.append(({k:[x*30/len(worlds) for x in v] for k,v in g.items()},
                                {k:[x*30/len(worlds) for x in v] for k,v in a.items()}))
        def collect(owner,deck,rng):
            self.assertEqual(s.rows,before) # both169-class strategies must remain frozen
            g,a=conditional[deck[0]];grads=[];avg=[]
            for k in g:
                o=SimpleNamespace(key=k,actions=oracle.ACTIONS[k[0]])
                if oracle.ACTOR[k[0]]==owner:grads.append((o,pi[k],g[k],0.))
                else:
                    weight=sum(a[k]);avg.append((o,[x/weight for x in a[k]],weight))
            return grads,avg
        s.collect=collect
        plan=[([i],[1,2],2*len(worlds)/30) for i,worlds in enumerate(strata)]
        with patch.object(module,'chance_plan',lambda rng:plan):self.assertEqual(s.batch(),2)
        for k in s.rows:
            for f,expected in (('R',expectedg),('S',expecteda)):
                for x,y,z in zip(s.rows[k][f],before[k][f],expected[k]):self.assertAlmostEqual(x,y+2*z,places=12)
    def test_adaptive_predictable_proposal_exact_expectation_and_weight_bound(self):
        p=[.1,.3,.6];q=adaptive_probabilities(p,[0,4,16],[True,False,True])
        self.assertAlmostEqual(sum(q),1);self.assertTrue(all(x>0 for x in q))
        values=[-7.,2.,13.]
        self.assertAlmostEqual(sum(a*(b/a)*v for a,b,v in zip(q,p,values)),sum(b*v for b,v in zip(p,values)))
        self.assertTrue(all(b/a<=5+1e-12 for a,b in zip(q,p)))
        self.assertAlmostEqual(sum(adaptive_probabilities(p,[0,4,16],[False]*3)),1)
    def test_actual_adaptive_pair_applies_chance_correction_to_R_and_S(self):
        s=CoverageSolver(None,None,adaptive=True);s.root_keys=[str(i) for i in range(169)]
        observed=[];o=SimpleNamespace(key='probe',actions=(0,1))
        def collect(owner,deck,rng):
            observed.append(deck)
            return ([(o,[.5,.5],[2.,-3.],0.)],[]) if owner==0 else ([],[(o,[.25,.75],7.)])
        s.collect=collect;s.step();self.assertEqual(observed[0],observed[1])
        k=next(i for i,g in enumerate(GROUPS) if tuple(sorted(observed[0][:2])) in [tuple(sorted(h)) for h in g])
        p=len(GROUPS[k])/1326;q=.2*p+.8/169;w=p/q
        self.assertAlmostEqual(s.rows['probe']['R'][0],2*w);self.assertAlmostEqual(s.rows['probe']['R'][1],-3*w)
        self.assertAlmostEqual(s.rows['probe']['S'][0],7*.25*w);self.assertAlmostEqual(s.rows['probe']['S'][1],7*.75*w)
        self.assertEqual(s.class_visits[k],1)

    def test_interrupted_batch_never_publishes_partial_rows(self):
        s=CoverageSolver(None,None);before=copy.deepcopy(s.rows)
        with self.assertRaises(TimeoutError):s.batch(timeout=-1)
        self.assertEqual(s.rows,before);self.assertEqual(s.macro_batches,0)

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class CoverageResume(unittest.TestCase):
    def test_adaptive_native_resume_RNG_and_priority_exact(self):
        from gto.qualification.build import load
        rules,native=load(os.environ['QUALIFICATION_BUILD']);a=CoverageSolver(rules,native,external=True,family=True,adaptive=True)
        a.step();d=json.loads(json.dumps(a.snapshot()));b=CoverageSolver(rules,native,external=True,family=True,adaptive=True);b.restore(d)
        a.step();b.step();self.assertEqual(a.snapshot(),b.snapshot())

    def test_family_warm_rows_unchanged_and_exact_resume(self):
        from gto.qualification.build import load
        from gto.qualification.action_baseline import ActionBaselineSolver
        rules,native=load(os.environ['QUALIFICATION_BUILD'])
        base=ActionBaselineSolver(rules,native,baseline=True,targeted=True)
        a=CoverageSolver(rules,native,family=True);a.adopt(base,18111);a.batch()
        b=CoverageSolver(rules,native,family=True);b.id={**b.id,'warm_source_digest':a.id['warm_source_digest']};b.restore(json.loads(json.dumps(a.snapshot())))
        self.assertEqual(a.snapshot(),b.snapshot())
        # Test continuation with short paired units; production batch remains169.
        a.step();b.step();self.assertEqual(a.snapshot(),b.snapshot());self.assertEqual(base.rows,{})


class FastCheckpoint(unittest.TestCase):
    def test_lossless_deterministic_and_failed_encoding_preserves_previous(self):
        import gzip,tempfile
        from pathlib import Path
        from gto.qualification.fast_checkpoint import save
        data={'R':[1e30,-1e-24,0.],'S':[.1,.9],'rng':random.Random(9).getstate(),'identity':{'a':'full'}}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.gz';save(p,data);before=p.read_bytes();save(p,data);self.assertEqual(before,p.read_bytes())
            self.assertEqual(json.loads(gzip.decompress(before)),json.loads(json.dumps(data)))
            with self.assertRaises(ValueError):save(p,{'bad':float('nan')})
            self.assertEqual(before,p.read_bytes());self.assertFalse(p.with_name(p.name+'.pending').exists())

if __name__=='__main__':unittest.main()
