"""Unbiased board-CF expectation, heldout stopping and N-owner native oracles."""
import copy,json,os,tempfile,unittest
from pathlib import Path
import numpy as np
from gto.qualification import fullstreet_solver as f,fullstreet_oracle as oracle
from gto.qualification.fullstreet_generalize import boards,stop
from gto.qualification.multiplayer_joint import Joint,pure_br,diagnostic_decks
from gto.qualification.multiplayer_scope import replay
from gto.qualification.build import load
from gto.native.training import NativeGame

class ChanceBoard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.temp=tempfile.TemporaryDirectory();cls.lib=f.build(Path(cls.temp.name))
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_sampled_board_expectation_matches_exact_mixture_and_path_oracle(self):
        q=oracle.fixture(self.lib,future=True)
        for _ in range(7):q.step()
        pi=q.policy(False)
        for p in (0,1):
            full=q.evaluate_owner(pi,p);expected=oracle.path_oracle(q,pi,p)
            accum=[np.zeros(q.S) for _ in range(3)];ev=0.;clairvoyant=0.
            for block in q.blocks:
                weight=block['weight'];one=dict(block,weight=1.);single=f.Game(self.lib,q.nodes,[one],2);m=single.evaluate_owner(pi,p)
                for a,v in zip(accum,(single.grad,single.avg,single.den)):a+=weight*v
                ev+=weight*m[0];clairvoyant+=weight*m[1]
            for a,b in zip(accum,expected):np.testing.assert_allclose(a,b,atol=2e-12)
            self.assertAlmostEqual(full[0],ev,places=12);self.assertLessEqual(full[1],clairvoyant+1e-12)
    def test_sampled_both_owner_updates_use_one_fixed_strategy(self):
        from gto.qualification.sampled_update import step
        q=oracle.fixture(self.lib,future=True)
        for _ in range(7):q.step()
        pi=q.policy(False);R=q.R.copy();A=q.A.copy();t=q.t
        expected=[oracle.path_oracle(q,pi,p) for p in (0,1)]
        step(q)
        for start,types,n,k in q.rows:
            owner=q.nodes[k]['actor'];sl=slice(start,start+types*n)
            np.testing.assert_allclose(q.R[sl],np.maximum(0,R[sl]+expected[owner][0][sl]),atol=1e-12)
            np.testing.assert_allclose(q.A[sl],A[sl]+(t+1)*expected[owner][1][sl],atol=1e-12)
    def test_splits_cannot_share_flops_and_rng_is_reproducible(self):
        train=boards(17120101,3);sel=boards(17120102,1,sum(train,[]));final=boards(17120103,1,sum(train+sel,[]))
        allboards=sum(train+sel+final,[]);flops=[tuple(x[:3]) for x in allboards]
        self.assertEqual(len(flops),len(set(flops)));self.assertEqual(train,boards(17120101,3))
        for public,group in zip(f.PUBLIC,train):self.assertTrue(all(f.public_code(x)==public for x in group))
    def test_first_nonimprovement_stops_instead_of_comparing_old_baseline(self):
        best=20.;seen=[]
        for x in (14.,15.,9.):
            seen.append(x)
            if stop(best,x):break
            best=x
        self.assertEqual(seen,[14.,15.]);self.assertEqual(best,14.)
        self.assertTrue(stop(14.,14.));self.assertFalse(stop(14.,13.))

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class MultiJoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):_,cls.native=load(os.environ['QUALIFICATION_BUILD'])
    def make(self,n=3):
        g=NativeGame([10]*n) if n==3 else NativeGame([10+2*(p%3) for p in range(n)],bba=2,rake_num=1,rake_den=20)
        return Joint(self.native,g,diagnostic_decks(n),[.5,.5])
    def test_all_players_complete_pure_br_matches_independent_enumeration(self):
        q=self.make()
        for _ in range(8):q.step()
        for p in range(3):self.assertAlmostEqual(q.br(q.policy(),p),pure_br(q,q.policy(),p),places=12)
    def test_N_owner_regret_and_average_match_independent_path_products(self):
        q=self.make()
        for _ in range(5):q.step()
        pi=q.policy(False);grad={k:np.zeros_like(v) for k,v in q.R.items()};avg={k:v.copy() for k,v in grad.items()}
        def value(k,w):
            n=q.nodes[k]
            if n['actor']<0:return n['utility'][w]
            return sum(pi[n['keys'][w]][a]*value(c,w) for a,c in enumerate(n['children']))
        def walk(k,w,reach):
            n=q.nodes[k];p=n['actor']
            if p<0:return
            key=n['keys'][w];v=value(k,w)[p];cf=q.weights[w]*np.prod([r for i,r in enumerate(reach) if i!=p])
            for a,c in enumerate(n['children']):grad[key][a]+=cf*(value(c,w)[p]-v)
            avg[key]+=q.weights[w]*reach[p]*pi[key]
            for a,c in enumerate(n['children']):
                rr=list(reach);rr[p]*=pi[key][a];walk(c,w,rr)
        for w in range(q.W):walk(0,w,[1.]*q.N)
        R=copy.deepcopy(q.R);A=copy.deepcopy(q.A);t=q.t;q.step()
        for k in pi:
            np.testing.assert_allclose(q.R[k],np.maximum(0,R[k]+grad[k]),atol=1e-12)
            np.testing.assert_allclose(q.A[k],A[k]+(t+1)*avg[k],atol=1e-12)
    def test_six_nine_native_profile_utilities_and_information_limits(self):
        for n in (6,9):
            q=self.make(n)
            for _ in range(8):q.step()
            m=q.measure();self.assertEqual(len(m['EV_bb']),n);self.assertGreaterEqual(min(m['restricted_gain_bb']),-1e-12);self.assertLessEqual(sum(m['EV_bb']),0)
            for key in q.actions:
                o=json.loads(key);self.assertEqual(len(o['own']),2);self.assertEqual(o['board'],[]);self.assertNotIn('holes',o)
            for d in diagnostic_decks(n):
                r=replay(self.native,q.game,q.profile(),deck=d,seed=17121)
                self.assertEqual(len(r['net_chips']),n);self.assertEqual(sum(r['net_chips']),-r['rake_chips'])
            self.assertIsNone(m['full_native_BR_upper']);self.assertIsNone(m['full_native_NashConv'])
    def test_N_player_BR_cannot_choose_using_hidden_world(self):
        q=object.__new__(Joint);q.N=3;q.W=2;q.weights=np.array([.5,.5]);q.t=0
        q.nodes=[dict(actor=2,actions=(0,1),keys=['same','same'],children=[1,2]),dict(actor=-1,children=[],utility=np.array([[0.,0.,1.],[0.,0.,-1.]])),dict(actor=-1,children=[],utility=np.array([[0.,0.,-1.],[0.,0.,1.]]))]
        q.actions={'same':(0,1)};q.owners={'same':2};q.R={'same':np.zeros(2)};q.A={'same':np.zeros(2)}
        pi=q.policy();self.assertEqual(q.br(pi,2),0.);self.assertEqual(pure_br(q,pi,2),0.)
        # A clairvoyant choice would gain1; the legal common infoset response is0.
        self.assertEqual(sum(q.weights[w]*max(q.nodes[c]['utility'][w,2] for c in (1,2)) for w in range(2)),1.)
    def test_checkpoint_resume_and_config_identity_fail_closed(self):
        q=self.make()
        for _ in range(8):q.step()
        with tempfile.TemporaryDirectory() as temp:
            state=q.export(Path(temp)/'state.json');other=self.make();other.restore(state);q.step();other.step()
            for k in q.R:np.testing.assert_array_equal(q.R[k],other.R[k]);np.testing.assert_array_equal(q.A[k],other.A[k])
            bad=copy.deepcopy(state);bad['R'][next(iter(bad['R']))][0]+=1
            with self.assertRaises(ValueError):other.restore(bad)
            other.identity['weights']=[.25,.75]
            with self.assertRaises(ValueError):other.restore(state)
if __name__=='__main__':unittest.main()
