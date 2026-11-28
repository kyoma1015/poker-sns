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
        posterior=j.conditional_opponent(g,list(s.policy),2,(0,))
        self.assertAlmostEqual(posterior['opponent_class_probability'][2],1.)
        self.assertFalse(posterior['own_reach_included'])
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
    def test_all_nine_matched_branches_keep_blind_cashflow(self):
        from gto.abstract.joint_reach_study import tree
        from gto.abstract import model
        ns,mapping,leaves=tree();original=model.tree()
        self.assertEqual(len(leaves),9)
        for old,start in leaves:
            pot=original[old]['value']
            if pot==100:
                self.assertEqual((ns[start]['c0'],ns[start]['c1']),(-50,100))
            else:
                terminal=start
                while ns[terminal]['actor']>=0:terminal=ns[terminal]['children'][0]
                self.assertEqual(ns[terminal]['c0'],-pot/2)
                self.assertEqual(ns[terminal]['c1'],pot)
        for old,n in enumerate(original):
            if n['actor']<0 and not n['matched']:self.assertEqual(ns[mapping[old]]['c0'],n['value']/2)
    def test_exact_private_group_engine_against_python_on_real_public_tree(self):
        from gto.abstract.joint_reach_study import tree
        ns,_,_=tree()
        ws=[world(mass=.25,equity=e,signals=s,flop=f) for e,s,f in [(.2,(0,8),(0,4,8)),(.8,(8,0),(0,4,8)),(.4,(0,8),(1,5,9)),(.6,(8,0),(1,5,9))]]
        g=j.prepare(ns,ws);solver=j.Solver(self.lib,g);r=solver.run(16)
        for owner,key in ((0,'sb_br_gain_bb'),(1,'bb_br_gain_bb')):
            self.assertAlmostEqual(j.independent_br(g,list(solver.policy),owner),r[key]+r['sb_ev_bb']*(1 if owner==0 else -1))
    def test_published_rows_and_posteriors_have_explicit_valid_support(self):
        import json,math
        from pathlib import Path
        from gto.abstract import fullsupport as fs
        r=json.loads(Path('docs/qa/joint-reach-20261107/results.json').read_text())
        self.assertEqual(r['formal_acceptance'],0);self.assertEqual(r['normal_GTO_ranges'],0)
        self.assertEqual(len(r['preflop_row_layout']),1690)
        for k in r['preflop_public_nodes']:
            self.assertEqual({c for n,c in r['preflop_row_layout'] if n==int(k)},set(range(169)))
        for packet in [p['frequency_then_action_ev_bb'] for p in r['preflop_packets']]+[r['frozen_coarse_small_same_subset']['preflop_frequency_then_action_ev_bb']]:
            values=fs.unpack(packet);offset=0
            for node,hand in r['preflop_row_layout']:
                n=len(r['preflop_public_nodes'][str(node)]['actions']);pi=values[offset:offset+n];ev=values[offset+n:offset+2*n];offset+=2*n
                self.assertAlmostEqual(math.fsum(pi),1)
                self.assertTrue(all(p>0 for p in pi)) # finite-sweep uniform support, no uncomputed0EV rows
                self.assertTrue(all(math.isfinite(v) and -50-1e-8<=v<=50+1e-8 for v in ev))
            self.assertEqual(offset,len(values))
        for p in r['TT_counterfactual_opponent_posterior'].values():
            self.assertFalse(p['own_reach_included']);self.assertGreater(p['counterfactual_mass'],0)
            self.assertAlmostEqual(math.fsum(p['opponent_class_probability']),1)

if __name__=='__main__':unittest.main()
