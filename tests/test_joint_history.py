import json,unittest
from pathlib import Path
from unittest.mock import patch
from gto.abstract import joint_history as h,joint_update_audit as g
class HistoryStudyTests(unittest.TestCase):
    def test_independent_lp_certificate_and_enumerated_response_equilibrium(self):
        records=json.loads(Path("docs/qa/joint-history-20261110/small-results.json").read_text())["games"]
        for equity,record in zip(h.EQUITIES,records):
            with patch.object(g,"EQUITY",equity):
                x=record["reference"];actual=h.measure(x["policy"]);self.assertLess(abs(x["dual_gap"]),1e-8);self.assertLess(actual["nc"],1e-8);self.assertAlmostEqual(actual["ev"],x["value"],delta=1e-8);self.assertEqual(x["pure_strategies_per_player"],64)
    def test_closed_cashflow_equals_independent_path_enumeration(self):
        pi=g.policies();expected=sum(g.WEIGHT[b]*g.oracle(b,p)['ev'] for b,p in enumerate(pi));self.assertAlmostEqual(h.ev(pi),expected,delta=1e-12)
    def test_actual_regret_average_and_behavior_resume_exactly(self):
        for order,damping in [('simultaneous',1.),('alternating',1.),('alternating',.25)]:
            x=h.Trainer()
            for _ in range(16):x.step(order,damping)
            checkpoint=json.loads(json.dumps(x.state()));y=h.Trainer.restore(checkpoint)
            for _ in range(16):x.step(order,damping);y.step(order,damping)
            self.assertEqual(x.state(),y.state());self.assertEqual(y.t,32)
            self.assertEqual(y.R[0][:8],y.R[1][:8]);self.assertEqual(y.S[0][:8],y.S[1][:8])
    def test_epsilon_reset_is_not_preserved_regret_history(self):
        x=h.Trainer()
        for _ in range(32):x.step()
        y=h.Trainer.restore(x.state());y.R=[[1e-15*z for z in p] for p in y.behavior];y.S=[[0.]*16 for _ in range(2)]
        self.assertEqual(x.behavior,y.behavior);self.assertNotEqual(x.R,y.R);self.assertNotEqual(x.S,y.S)
    def test_realization_mixture_payoff_affine_for_one_player(self):
        left=g.policies();right=[list(reversed(p)) for p in left];right[1][:8]=right[0][:8]
        for owner in (0,1):
            fixed=[[right[b][j] if h.OWNER(j)==owner else left[b][j] for j in range(16)] for b in range(2)]
            for w in (0.,.25,.5,1.):
                mixed=h.realization_mix(left,fixed,w);self.assertAlmostEqual(h.ev(mixed),(1-w)*h.ev(left)+w*h.ev(fixed),delta=1e-12)
    def test_pointwise_mixing_is_not_sequence_form_mixing(self):
        left=g.policies();right=[list(reversed(p)) for p in left];right[1][:8]=right[0][:8];right=[[right[b][j] if h.OWNER(j)==0 else left[b][j] for j in range(16)] for b in range(2)]
        pointwise=[[(a+b)/2 for a,b in zip(x,y)] for x,y in zip(left,right)];correct=h.realization_mix(left,right,.5)
        self.assertGreater(abs(h.ev(pointwise)-h.ev(correct)),1e-4)
    def test_future_board_preflop_policy_rejected(self):
        bad=g.policies();bad[1][:2]=[.9,.1]
        with self.assertRaisesRegex(ValueError,"future-board"):h.measure(bad)
        with self.assertRaisesRegex(ValueError,"future-board"):h.realization_mix(g.policies(),bad,.25)
    def test_damped_variant_is_explicit_and_invalid_budget_rejected(self):
        self.assertEqual(h.CANDIDATES['alt_damped_experimental'][-1],.25)
        with self.assertRaises(ValueError):h.Trainer().step(damping=0)
        with self.assertRaises(ValueError):h.realization_mix(g.policies(),g.policies(),1.1)
if __name__=='__main__':unittest.main()
