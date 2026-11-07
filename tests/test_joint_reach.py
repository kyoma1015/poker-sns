import tempfile
import unittest
from gto.abstract import joint_reach as j

def node(actor,children=(),c0=0.,c1=0.,street='preflop'):
    return dict(actor=actor,children=list(children),c0=c0,c1=c1,street=street)

def world(mass=.5,equity=0.,signals=(0,8),flop=(0,4,8)):
    return dict(mass=mass,equity=equity,signals=signals,flop=flop)

class JointReachTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.lib=j.build(cls.tmp.name)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_future_board_is_not_preflop_information(self):
        ns=[node(0,[1,2]),node(-1,c0=-1,c1=2),node(-1,c0=1,c1=-2)]
        g=j.prepare(ns,[world(equity=0),world(equity=1,flop=(1,5,9))]);s=j.Solver(self.lib,g);r=s.run(0)
        self.assertAlmostEqual(r['joint_nashconv_bb'],0)
        self.assertAlmostEqual(j.independent_br(g,list(s.policy),0),0)
        self.assertEqual(g['info'][0],g['info'][1])
    def test_public_flop_can_select_later_actions(self):
        ns=[node(0,[1,2],street='flop'),node(-1,c0=-1,c1=2),node(-1,c0=1,c1=-2)]
        g=j.prepare(ns,[world(equity=0),world(equity=1,flop=(1,5,9))]);s=j.Solver(self.lib,g);r=s.run(0)
        self.assertAlmostEqual(r['joint_nashconv_bb'],1)
    def test_hidden_opponent_does_not_select_own_action(self):
        n=node(0);a=world();b=world(signals=(0,999))
        self.assertEqual(j.observation(n,a),j.observation(n,b))
        n['street']='flop';self.assertEqual(j.observation(n,a),j.observation(n,b))
    def test_own_zero_reach_does_not_remove_regret_update(self):
        ns=[node(0,[1,2]),node(-1),node(0,[3,4]),node(-1,c0=-1),node(-1,c0=2)]
        g=j.prepare(ns,[world(mass=1)]);s=j.Solver(self.lib,g)
        s.regret[g['info'][0]]=100 # Own probability of entering node2 is zero.
        s.run(1);i=g['info'][2]
        self.assertGreater(s.regret[i+1],0)
        self.assertAlmostEqual(s.sums[i]+s.sums[i+1],0)
    def test_opponent_reach_controls_posterior_and_br(self):
        ns=[node(1,[1,2]),node(-1),node(0,[3,4]),node(-1,c1=1),node(-1,c0=1,c1=-1)]
        g=j.prepare(ns,[world(equity=0),world(equity=1,signals=(0,16))]);s=j.Solver(self.lib,g)
        # Opponent enters only for equity=1; own BR must choose first action.
        a,b=g['info'][0],g['info'][1];s.sums[a]=1;s.sums[b+1]=1
        r=s.run(0);self.assertAlmostEqual(r['sb_br_gain_bb'],.25)
        self.assertAlmostEqual(j.independent_br(g,list(s.policy),0),.5)
    def test_native_python_br_and_regret_bound(self):
        ns=[node(0,[1,4]),node(1,[2,3]),node(-1,c0=-2,c1=4),node(-1,c0=1,c1=-2),node(-1,c0=-.2)]
        g=j.prepare(ns,[world(equity=.1),world(equity=.8,signals=(8,0))]);s=j.Solver(self.lib,g)
        for count in (1,15,48):
            r=s.run(count)
            self.assertAlmostEqual(j.independent_br(g,list(s.policy),0),r['sb_ev_bb']+r['sb_br_gain_bb'])
            self.assertAlmostEqual(j.independent_br(g,list(s.policy),1),-r['sb_ev_bb']+r['bb_br_gain_bb'])
            self.assertLessEqual(r['joint_nashconv_bb'],r['positive_regret_bound_bb']+1e-8)
    def test_reject_imperfect_recall(self):
        ns=[node(0,[1]),node(0,[2],street='flop'),node(-1)]
        # Artificial observation key forgets a known starting class.
        from unittest.mock import patch
        real=j.observation
        with patch.object(j,'observation',lambda n,w:(0,) if n['street']=='flop' else real(n,w)):
            with self.assertRaisesRegex(ValueError,'imperfect recall'):j.prepare(ns,[world(),world(signals=(8,0))])
    def test_reject_nonprobability_chance_and_shared_public_child(self):
        with self.assertRaises(ValueError):j.prepare([node(-1)],[world(mass=.2)])
        with self.assertRaises(ValueError):j.prepare([node(0,[1,1]),node(-1)],[world(mass=1)])

if __name__=='__main__':unittest.main()
