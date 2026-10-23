"""Exact initial-deal provenance and actual reconstructed-native consistency."""
import importlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest
from fractions import Fraction
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from gto.native.initial_chance_reach import initial_chance_export, ordered_hand_marginal
from gto.native.hand169_bridge import context_of
from gto.native.training import NativeGame,train_batch

class InitialReach(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR'])
        cls.native=importlib.import_module('pokerid_g12')

    def game(self,n=2):return NativeGame([4]*n,bb=2,bba=0,rake_num=0,rake_den=1)
    def solver(self,g,seed=17,iterations=200):
        s=self.native.Solver(g,.6,seed,True,True,.1)
        for _ in range(iterations):s.run_iteration()
        return s
    def context(self,g):
        st=self.native.NativeState(g)
        for a in range(2*g.num_players()):st.apply_action(a)
        return context_of(st.information_state_string(st.current_player()))

    def test_exact_combinatorial_probability_all_counts(self):
        for n in range(2,10):
            self.assertEqual(ordered_hand_marginal(n),Fraction(math.perm(50,2*n-2),math.perm(52,2*n)))
            self.assertEqual(ordered_hand_marginal(n),Fraction(1,2652))

    def test_native_initial_actors_and_contexts_2_to_9(self):
        for n in range(2,10):
            with self.subTest(players=n):
                g=self.game(n);s=self.solver(g,iterations=2)
                r=initial_chance_export(self.native,s,g,self.context(g))
                self.assertEqual(r['reach_evidence']['players'],n)
                self.assertEqual(r['reach_evidence']['seat'],0 if n==2 else 2)
                self.assertEqual(r['reach_evidence']['ordered_hand_probability'],{'numerator':1,'denominator':2652})
                self.assertTrue(all(x['ev'] is None for x in r['hands'].values()))

    def test_complete_native_1326_policy_coverage_with_exact_mass(self):
        g=self.game();s=self.solver(g,iterations=20000)
        before=(s.rng_state(),s.iteration)
        r=initial_chance_export(self.native,s,g,self.context(g))
        self.assertEqual((s.rng_state(),s.iteration),before)
        self.assertTrue(r['complete'])
        self.assertTrue(r['reach_evidence']['complete_ordered_coverage'])
        self.assertEqual(r['observed_infosets'],2652)
        self.assertEqual(r['concrete_combinations'],1326)
        self.assertEqual(len(r['hands']),169)
        self.assertAlmostEqual(sum(x['reach_mass'] for x in r['hands'].values()),1)
        self.assertAlmostEqual(r['hands']['AA']['reach_mass'],6/1326)
        self.assertAlmostEqual(r['hands']['AKs']['reach_mass'],4/1326)
        self.assertAlmostEqual(r['hands']['AKo']['reach_mass'],12/1326)
        self.assertIn('proven',r['weight_provenance'])

    def test_checkpoint_resume_preserves_policy_rng_and_provenance(self):
        g=self.game();direct=self.solver(g,iterations=400)
        split=self.solver(g,iterations=0)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            train_batch(split,g,200,p/'first')
            resumed=self.solver(g,iterations=0)
            train_batch(resumed,g,200,p/'second',resume=p/'first')
            self.assertEqual(resumed.rng_state(),direct.rng_state())
            self.assertEqual(resumed.iteration,direct.iteration)
            a=initial_chance_export(self.native,direct,g,self.context(g))
            b=initial_chance_export(self.native,resumed,g,self.context(g))
            self.assertEqual(a,b)

    def test_wrong_seat_is_rejected(self):
        g=self.game();s=self.solver(g);c=self.context(g);c['seat']=1
        with self.assertRaises(ValueError):initial_chance_export(self.native,s,g,c)

    def test_nonempty_history_has_no_claimed_chance_only_proof(self):
        g=self.game();s=self.solver(g);c=self.context(g);c['betting_history']=[[0,0,1,2,2]]
        with self.assertRaises(ValueError):initial_chance_export(self.native,s,g,c)

    def test_public_config_mismatch_is_rejected(self):
        g=self.game();s=self.solver(g);c=self.context(g)
        c['public_config']=json.loads(json.dumps(c['public_config']));c['public_config']['stacks']=[6,4]
        with self.assertRaises(ValueError):initial_chance_export(self.native,s,g,c)

    def test_runtime_config_drift_is_rejected(self):
        g=self.game();s=self.solver(g);c=self.context(g);g.stacks[0]=6
        with self.assertRaises(ValueError):initial_chance_export(self.native,s,g,c)

    def test_root_action_or_fixture_restriction_is_rejected(self):
        for field,value in [('root_actions',[48]),('fixture',{'hole_deck':[0,1,2,3],'board':[4,5,6,7,8]})]:
            g=self.game();s=self.solver(g);c=self.context(g);setattr(g,field,value)
            with self.assertRaises(ValueError):initial_chance_export(self.native,s,g,c)

    def test_native_action_identity_mismatch_is_rejected(self):
        # Deliberately stale public-config string with a mutated six-chip stack:
        # real native solver rows offer extra raises; clean 4/4 game must reject.
        dirty=self.game();dirty.stacks[0]=6
        s=self.solver(dirty,iterations=200)
        clean=self.game()
        with self.assertRaises(ValueError):initial_chance_export(self.native,s,clean,self.context(clean))

if __name__=='__main__':unittest.main()
