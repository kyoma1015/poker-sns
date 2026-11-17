import copy,json,math,os,random,unittest
from gto.qualification.average_support import AverageSupportSolver
from gto.qualification.native_mccfr import Solver
from gto.qualification.build import load

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class AverageSupport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rules,cls.native=load(os.environ['QUALIFICATION_BUILD'])

    def test_zero_opponent_support_average_is_reachable_only_via_exploring_opponent(self):
        # Root SB target ALWAYS folds. BB's own realization reach at any vs-open
        # infoset remains1. Legacy BB-owner average can never visit these states.
        class Correct(AverageSupportSolver):
            def row(self,o,average=False):
                return [float(a==0) for a in o.actions] if not o.history else [1/len(o.actions)]*len(o.actions)
        deck=list(range(9));correct=Correct(self.rules,self.native)
        captured=[]
        for seed in range(8):
            _,avg=correct.collect(0,deck,random.Random(seed))
            captured += [(o,pi,w) for o,pi,w in avg if o.actor==1 and len(o.history)==1]
        self.assertTrue(captured)
        qroot=.6/99
        for o,pi,w in captured:
            self.assertAlmostEqual(qroot*w,1.)
            for p in pi:self.assertAlmostEqual(qroot*w*p,p)
        control=Correct(self.rules,self.native,correct=False)
        for seed in range(8):
            _,avg=control.collect(1,deck,random.Random(seed))
            self.assertEqual(avg,[]) # ZERO, not the required positive row.

    def test_other_average_expectation_matches_exact_realization_sum_with_zero_target(self):
        from gto.abstract.matched_history import python_oracle
        # Opponent root has a zero-target branch; own downstream strategy must
        # still be averaged with own reach1, not opponent reach0.
        ns=[dict(actor=0,children=[1,2]),dict(actor=-1,children=[],c0=0,c1=0),
            dict(actor=1,children=[3,4]),dict(actor=-1,children=[],c0=2,c1=0),
            dict(actor=-1,children=[],c0=-3,c1=0)]
        g=dict(nodes=ns,worlds=[dict(mass=1.,equity=0.)],info=[0,0,2,0,0]);pi=[1.,0.,.3,.7]
        exact=python_oracle(g,pi)
        # Traverser0 exploration enters branch1 with q=.3. collect's actual
        # native boundary above checks this same weight on real observations.
        corrected=[.3*(p/.3) for p in pi[2:]]
        for a in range(2):self.assertAlmostEqual(corrected[a],exact['avg'][2+a])
        self.assertNotEqual([0.,0.],exact['avg'][2:])

    def test_control_and_corrected_use_identical_regret_updates(self):
        source=Solver(self.rules,self.native)
        for _ in range(4):source.step()
        a=AverageSupportSolver(self.rules,self.native,correct=False);a.migrate(source.snapshot())
        b=AverageSupportSolver(self.rules,self.native,correct=True);b.migrate(source.snapshot())
        for _ in range(16):a.step();b.step()
        nonzero=lambda s:{k:v['R'] for k,v in s.rows.items() if any(v['R'])}
        self.assertEqual(nonzero(a),nonzero(b));self.assertEqual(a.rng.getstate(),b.rng.getstate())
        self.assertNotEqual(a.average_counts,b.average_counts)

    def test_resume_source_preservation_and_frozen_pair(self):
        source=Solver(self.rules,self.native)
        for _ in range(4):source.step()
        saved=source.snapshot();original=copy.deepcopy(saved)
        a=AverageSupportSolver(self.rules,self.native);a.migrate(saved)
        self.assertEqual(saved,original)
        self.assertTrue(all(not any(r['S']) for r in a.rows.values()))
        self.assertTrue(any(any(r['R']) for r in a.rows.values()))
        collect=a.collect;before=copy.deepcopy(a.rows)
        def watched(*args):self.assertEqual(a.rows,before);return collect(*args)
        a.collect=watched;a.step();a.collect=collect
        b=AverageSupportSolver(self.rules,self.native);b.restore(json.loads(json.dumps(a.snapshot())))
        for _ in range(4):a.step();b.step()
        self.assertEqual(a.snapshot(),b.snapshot());self.assertTrue(a.average_counts)

if __name__=='__main__':unittest.main()
