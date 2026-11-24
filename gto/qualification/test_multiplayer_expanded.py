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


@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class SparseNJoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):_,cls.native=load(os.environ['QUALIFICATION_BUILD'])
    def make(self,**kw):
        from gto.qualification.multiplayer_joint import SparseJoint
        return SparseJoint(self.native,NativeGame([24,22,20]),decks=expanded_decks(3),weights=[.25]*4,**kw)
    def exact(self):return Joint(self.native,NativeGame([24,22,20]),expanded_decks(3),[.25]*4,action_scope='preflop')
    def test_exact_expected_N_owner_CF_average_with_zero_targets(self):
        import random
        q=self.exact();s=self.make(max_seconds=30);pi=q.policy(False)
        for i,(k,v) in enumerate(pi.items()):
            if len(v)>1 and i%2==0:pi[k]=np.eye(len(v))[i%len(v)]
        oracle=path_oracle(q,pi);G={k:np.zeros_like(v) for k,v in pi.items()};A={k:v.copy() for k,v in G.items()}
        for owner in range(3):
            for deck,w in zip(expanded_decks(3),[.25]*4):
                batch=s.collect(owner,deck,random.Random(171242),pi,audit=True)
                for k,v in batch['grad'].items():G[k]+=w*v
                for k,v in batch['avg'].items():A[k]+=w*v/2
        for k in pi:
            np.testing.assert_allclose(G[k],oracle['grad'][k],atol=1e-11)
            np.testing.assert_allclose(A[k],oracle['avg'][k],atol=1e-11)
        # Seat2(root)targetfold=1: itscalltarget0 still must support seat0 average
        # when seat1 traverses. The OTHER nonowner's zero would break q=pi.
        pi=q.policy(False)
        for key in q.nodes[0]['keys']:pi[key]=np.array([1.,0.,0.])
        owner0node=q.nodes[q.nodes[0]['children'][q.nodes[0]['actions'].index(1)]]
        batch=s.collect(1,expanded_decks(3)[0],random.Random(1),pi,audit=True)
        self.assertGreater(sum(batch['avg'][owner0node['keys'][0]]),0.)
    def test_all_owners_share_frozen_preupdate_policy_before_atomic_commit(self):
        import random
        q=self.exact();s=self.make();s.actions=q.actions.copy();s.owners=q.owners.copy()
        s.R={k:np.arange(1,len(v)+1,dtype=float) for k,v in q.R.items()};s.A={k:np.zeros_like(v) for k,v in s.R.items()};s.R_visits={k:0 for k in s.R};s.A_visits=s.R_visits.copy()
        beforeR=copy.deepcopy(s.R);beforeA=copy.deepcopy(s.A);fixed=s.policy(False);seen=[];collect=s.collect
        def record(owner,deck,stream,pi,**kw):
            for k in beforeR:np.testing.assert_array_equal(s.R[k],beforeR[k]);np.testing.assert_array_equal(s.A[k],beforeA[k]);np.testing.assert_array_equal(pi[k],fixed[k])
            b=collect(owner,deck,stream,pi,**kw);seen.append((tuple(deck),b));return b
        s.collect=record;s.step();self.assertEqual(len(seen),3);self.assertEqual(len(set(x[0] for x in seen)),1)
        grad={k:np.zeros_like(v) for k,v in s.R.items()};avg={k:v.copy() for k,v in grad.items()}
        for _,b in seen:
            for k,v in b['grad'].items():grad[k]+=v
            for k,v in b['avg'].items():avg[k]+=v/2
        for k in s.R:
            np.testing.assert_array_equal(s.R[k],np.maximum(0,beforeR[k]+grad[k]));np.testing.assert_array_equal(s.A[k],beforeA[k]+avg[k])
    def test_cap_rolls_back_R_A_and_nextdraw_RNG_then_exact_resume(self):
        import gzip
        s=self.make(max_nodes=1);before=s.state()
        with self.assertRaisesRegex(ValueError,'cap'):s.step()
        self.assertEqual(s.state(),before);s.max_nodes=20000;s.step()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'state.json.gz';s.export(path);other=self.make();other.restore(json.loads(gzip.decompress(path.read_bytes())))
            s.step();other.step();self.assertEqual(s.state(),other.state())
            with self.assertRaises(FileExistsError):s.export(path)
    def test_six_nine_sparse_batch_and_unseen_legal_native_profile(self):
        import random
        from gto.qualification.multiplayer_joint import SparseJoint
        from gto.qualification.multiplayer_scope import replay
        for n in (6,9):
            game=NativeGame([100-20*(p%3) for p in range(n)],bba=2,rake_num=1,rake_den=20)
            s=SparseJoint(self.native,game,seed=171242,max_seconds=30);r=s.step()
            self.assertGreater(r['nodes'],0);self.assertLess(r['infosets'],20000)
            result=replay(self.native,game,s.profile(),deck=random.Random(n).sample(range(52),52),seed=171245)
            self.assertEqual(len(result['net_chips']),n);self.assertEqual(sum(result['net_chips']),-result['rake_chips'])
            self.assertFalse(result['ordinary_registry_admission']);self.assertIsNone(result['NashConv'])
    def test_canonical_preflop_profile_reuses_suit_orbit_and_omits_forced_rows(self):
        from dataclasses import replace
        from gto.qualification.multiplayer_joint import sparse_key,observation
        s=self.make();state=self.native.NativeState(s.game)
        for card in expanded_decks(3)[0][:6]:state.apply_action(card)
        o=observation(state);alt=replace(o,own=tuple(4*(c//4)+(c%4+2)%4 for c in o.own))
        self.assertEqual(sparse_key(o),sparse_key(alt));actions=tuple(a for a in o.actions if a in (0,1) or a==8)
        key=sparse_key(o);s.actions[key]=actions;s.owners[key]=o.actor;s.R[key]=np.zeros(len(actions));s.A[key]=np.eye(len(actions))[0];s.R_visits[key]=0;s.A_visits[key]=1
        response=s.profile().response.provider(alt);self.assertEqual(response[actions[0]],1.)
        fresh=self.make();fresh.step();self.assertTrue(all(len(a)>1 for a in fresh.actions.values()))
    def test_lazy_average_matches_full_oracle_including_prediscovery_and_resumes(self):
        from gto.qualification.native_mccfr import digest
        exact=self.exact();sampled=self.make(seed=171245,average_mode='sampled',max_seconds=30);lazy=self.make(seed=171245,average_mode='lazy',max_seconds=30)
        expected={k:np.zeros(len(v)) for k,v in exact.actions.items()};worst=0.
        for iteration in range(1,9):
            pi={k:lazy.policy(False).get(k,np.ones(len(a))/len(a)) for k,a in exact.actions.items()};oracle=path_oracle(exact,pi)
            for k,v in oracle['avg'].items():expected[k]+=iteration*v
            sampled.step();lazy.step();self.assertEqual(set(sampled.R),set(lazy.R));self.assertEqual(sampled.rng.getstate(),lazy.rng.getstate())
            for k in lazy.R:
                np.testing.assert_array_equal(sampled.R[k],lazy.R[k]);np.testing.assert_allclose(lazy.A[k],expected[k],atol=2e-11)
                worst=max(worst,float(np.max(abs(lazy.A[k]-expected[k]))))
        clone=self.make(seed=171245,average_mode='lazy',max_seconds=30);clone.restore(json.loads(json.dumps(lazy.state())))
        lazy.step();clone.step();self.assertEqual(lazy.state(),clone.state())
        bad=lazy.state();next(iter(bad['lazy_info'].values()))['mass']=2.;bad['digest']=digest({k:v for k,v in bad.items() if k!='digest'})
        with self.assertRaises(ValueError):clone.restore(bad)
        self.assertLess(worst,2e-11)
    def test_trajectory_proposal_retains_tiny_positive_zero_target_support(self):
        import random
        exact=self.exact();pi=exact.policy(False)
        for key in exact.nodes[0]['keys']:pi[key]=np.array([1.,0.,0.])
        node=exact.nodes[exact.nodes[0]['children'][exact.nodes[0]['actions'].index(1)]]
        sampler=self.make(proposal='trajectory',epsilon=1e-20,max_seconds=30)
        batch=sampler.collect(1,expanded_decks(3)[0],random.Random(1),pi,audit=True)
        self.assertGreater(sum(batch['avg'][node['keys'][0]]),0.)
        self.assertTrue(all(np.all(np.isfinite(v)) for d in (batch['grad'],batch['avg']) for v in d.values()))
    def test_checkpoint_tamper_owner_and_invalid_chance_fail_closed(self):
        from gto.qualification.multiplayer_joint import SparseJoint
        from gto.qualification.native_mccfr import digest
        s=self.make();s.step();state=s.state();bad=copy.deepcopy(state);bad['owners'][next(iter(bad['owners']))]=3
        bad['digest']=digest({k:v for k,v in bad.items() if k!='digest'})
        with self.assertRaises(ValueError):self.make().restore(bad)
        with self.assertRaises(ValueError):SparseJoint(self.native,s.game,decks=expanded_decks(3),weights=[float('nan')]*4)
        with self.assertRaises(ValueError):self.make(epsilon=0)

if __name__=='__main__':unittest.main()
