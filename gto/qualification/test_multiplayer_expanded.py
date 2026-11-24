"""Expanded finite N-owner native paths; not fullNLHE/registry qualification."""
import copy,json,os,tempfile,unittest
from pathlib import Path
import numpy as np
from gto.qualification.build import load
from gto.native.training import NativeGame
from gto.qualification.multiplayer_joint import Joint,expanded_decks,path_oracle,path_br

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class ExpandedJoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):_,cls.native=load(os.environ['QUALIFICATION_BUILD'])
    def make(self,**kwargs):return Joint(self.native,NativeGame([24,22,20],**kwargs),expanded_decks(3),[.25]*4,max_nodes=5000,action_scope='preflop')
    def leaf(self,q,actions):
        k=0
        for a in actions:
            node=q.nodes[k];self.assertIn(a,node['actions']);k=node['children'][node['actions'].index(a)]
        while q.nodes[k]['actor']>=0:
            self.assertEqual(q.nodes[k]['actions'],(1,));k=q.nodes[k]['children'][0]
        return q.nodes[k]['utility']
    def test_native_RFI_threebet_short_allin_and_allstreet_own_public_keys(self):
        q=self.make();rounds=set();decks=expanded_decks(3)
        self.assertTrue(any(n.get('actions')==(0,1,8) for n in q.nodes))
        self.assertTrue(any(22 in n.get('actions',()) for n in q.nodes))
        self.assertTrue(any(24 in n.get('actions',()) for n in q.nodes))
        for n in q.nodes:
            if n['actor']<0:continue
            for w,key in enumerate(n['keys']):
                o=json.loads(key);p=o['actor'];rounds.add(o['round'])
                self.assertEqual(o['own'],sorted(decks[w][2*p:2*p+2]));self.assertNotIn('holes',o);self.assertNotIn('world',o)
                self.assertEqual(o['board'],decks[w][6:6+(0,3,4,5)[o['round']]])
                self.assertTrue(set(n['actions']).issubset(o['actions']))
                if o['round']>0:self.assertEqual(n['actions'],(1,))
        self.assertEqual(rounds,{0,1,2,3})
    def test_different_actual_hidden_payoffs_and_lawful_BR(self):
        q=self.make();pi=q.policy()
        # Same rootQQ/preflop observation in worlds0,1,3; different unknown runouts.
        self.assertEqual(q.nodes[0]['keys'][0],q.nodes[0]['keys'][1])
        expected=np.array([[42,-22,-20],[-22,42,-20],[-22,42,-20],[-22,-18,40]])/2
        np.testing.assert_array_equal(self.leaf(q,[8,22,24,1,1]),expected)
        for p in range(3):
            lawful=path_br(q,pi,p);self.assertAlmostEqual(q.br(pi,p),lawful,places=11)
            def clair(k,w):
                n=q.nodes[k]
                if n['actor']<0:return n['utility'][w,p]
                vals=[clair(c,w) for c in n['children']]
                return max(vals) if n['actor']==p else sum(pi[n['keys'][w]][a]*v for a,v in enumerate(vals))
            invalid=sum(q.weights[w]*clair(0,w) for w in range(q.W))
            self.assertGreater(invalid,lawful+.01)
        self.assertAlmostEqual(path_br(q,pi,2),0.,places=12)
    def test_terminal_path_regret_average_and_EV_match_vector_update(self):
        q=self.make()
        for i,(key,value) in enumerate(q.R.items()):q.R[key]=np.array([0. if (i+a)%5==0 else 1.+(i+a)%3 for a in range(len(value))])
        pi=q.policy(False);o=path_oracle(q,pi)
        np.testing.assert_allclose(o['EV'],q.weights@q.values(pi)[0],atol=1e-11)
        R=copy.deepcopy(q.R);A=copy.deepcopy(q.A);t=q.t;q.step()
        for k in R:
            np.testing.assert_allclose(q.R[k],np.maximum(0,R[k]+o['grad'][k]),atol=1e-11)
            np.testing.assert_allclose(q.A[k],A[k]+(t+1)*o['avg'][k],atol=1e-11)
    def test_independent_cashflow_refund_ante_rake_unequalstacks(self):
        q=self.make()
        np.testing.assert_array_equal(self.leaf(q,[8,0,0]),np.tile([-.5,-1.,1.5],(4,1)))
        # Caller/refund counterpart: soleRFI6 vs blinds1/2 refunds4; trueprofit3.
        cash=self.make(bba=2,rake_num=1,rake_den=20)
        # Contributions20/20/20+BBdead2=62; floor5%rake3, payout59.
        expected=np.array([[39,-22,-20],[-20,37,-20],[-20,37,-20],[-20,-22,39]])/2
        np.testing.assert_array_equal(self.leaf(cash,[8,22,1,1]),expected)
        np.testing.assert_array_equal(expected.sum(axis=1),np.full(4,-1.5))
        # Preflop folds remain no-flop-no-drop even with the BBdeadante.
        np.testing.assert_array_equal(self.leaf(cash,[8,0,0]),np.tile([-.5,-2.,2.5],(4,1)))
    def test_expanded_checkpoint_resume_and_legacy_scope_stays_available(self):
        q=self.make()
        for _ in range(4):q.step()
        with tempfile.TemporaryDirectory() as d:
            state=q.export(Path(d)/'new-state.json');other=self.make();other.restore(state)
            q.step();other.step()
            for k in q.R:np.testing.assert_array_equal(q.R[k],other.R[k]);np.testing.assert_array_equal(q.A[k],other.A[k])
            legacy=Joint(self.native,q.game,expanded_decks(3),[.25]*4)
            with self.assertRaises(ValueError):legacy.restore(state)
        self.assertIsNone(q.measure()['full_native_BR_upper'])
    def test_native_profile_replays_same_finite_fullstreet_paths(self):
        from gto.qualification.multiplayer_scope import replay
        q=self.make();decks=expanded_decks(3)
        # Shared-infoset deterministic profiles, never select using worldindex.
        for mode in ('raise','call'):
            for key,acts in q.actions.items():
                a=acts.index(max(acts)) if mode=='raise' else acts.index(1)
                q.A[key]=np.eye(len(acts))[a]
            values=q.values(q.policy())[0];profile=q.profile()
            for w,deck in enumerate(decks):
                r=replay(self.native,q.game,profile,deck=deck,seed=171241)
                np.testing.assert_array_equal(np.array(r['net_chips'])/2,values[w])
                self.assertFalse(r['ordinary_registry_admission'])

    def test_cards_weights_and_six_nine_tree_cap_fail_closed(self):
        for n in (3,6,9):
            decks=expanded_decks(n)
            for d in decks:self.assertEqual(len(d),52);self.assertEqual(set(d),set(range(52)))
        with self.assertRaises(ValueError):Joint(self.native,NativeGame([24,22,20]),expanded_decks(3),[float('nan')]*4,action_scope='preflop')
        for n in (6,9):
            with self.assertRaisesRegex(ValueError,'tree/time cap'):
                Joint(self.native,NativeGame([24-2*(p%3) for p in range(n)]),expanded_decks(n),[.25]*4,max_nodes=2,action_scope='preflop')

if __name__=='__main__':unittest.main()
