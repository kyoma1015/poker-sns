"""Causal fullstreet joint game: independent path/BR and native cashflow oracles."""
import copy,ctypes,gzip,itertools,json,os,tempfile,unittest
from pathlib import Path
import numpy as np
from gto.abstract import model
from gto.qualification import fullstreet_solver as f,fullstreet_oracle as oracle
from gto.qualification.policy import act,sha
from gto.qualification.native_mccfr import betting
from gto.qualification.public_response import observe
from gto.qualification.preflop_release_solver import load_policy
from gto.native.training import NativeGame

class FullstreetExact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.temp=tempfile.TemporaryDirectory();cls.lib=f.build(Path(cls.temp.name))
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_complete_br_and_convergence_in_three_games(self):
        target=Path(self.temp.name)/'exact.json';self.assertTrue(f.study_exact(self.lib,target))
        for case in json.loads(target.read_text())['cases']:
            self.assertLess(case['curve'][-1]['NC_bb'],.0001)
    def test_current_reach_regret_average_matches_independent_path_products(self):
        for future in (False,True):
            q=oracle.fixture(self.lib,future=future)
            for _ in range(17):q.step()
            pi=q.policy(False)
            for owner in (0,1):
                ev,br=q.evaluate_owner(pi,owner)
                self.assertAlmostEqual(ev,(1 if owner==0 else -1)*oracle.reference(q,pi),places=12)
                self.assertAlmostEqual(br,oracle.pure_br(q,pi,owner),places=12)
                for actual,expected in zip((q.grad,q.avg,q.den),oracle.path_oracle(q,pi,owner)):
                    np.testing.assert_allclose(actual,expected,atol=2e-12)
    def test_future_suffix_not_visible_at_preflop_or_flop(self):
        q=oracle.fixture(self.lib,future=True);worlds=oracle.worlds(q)
        same=[w for w in worlds if w['classes']==(0,1)]
        self.assertGreater(len(same),1)
        self.assertEqual(oracle.key(q,0,same[0]),oracle.key(q,0,same[1]))
        self.assertEqual(oracle.key(q,4,same[0]),oracle.key(q,4,same[1]))
        self.assertNotEqual(oracle.key(q,6,same[0]),oracle.key(q,6,same[1]))
        self.assertEqual(f.public_code([0,5,10]),0)
        self.assertEqual(f.public_code([0,5,10,12,1]),1)
        self.assertEqual(f.public_code([0,5,10,1,12]),3)
    def test_real_regret_average_checkpoint_resume_is_bit_exact(self):
        q=oracle.fixture(self.lib,future=True)
        for _ in range(19):q.step()
        target=Path(self.temp.name)/'resume.npz';q.save(target);other=oracle.fixture(self.lib,future=True);other.restore(target)
        q.step();other.step()
        for a,b in ((q.R,other.R),(q.A,other.A),(q.visits,other.visits),(q.policy(),other.policy())):np.testing.assert_array_equal(a,b)
        self.assertEqual(q.t,other.t)
        other.visits[:]=65535;other.step();self.assertEqual(int(other.visits.max()),65535)
    def test_chance_weights_card_removal_and_showdown_symmetry(self):
        self.assertAlmostEqual(float(f.WEIGHTS.sum()),1.)
        board=[0,5,10,15,20];block=f.moment(self.lib,board,1.)
        M=np.asarray(block['mass']);E=np.asarray(block['equity'])
        self.assertAlmostEqual(float(M.sum()),1.)
        np.testing.assert_allclose(M,M.T,atol=1e-15)
        np.testing.assert_allclose(M*E+(M*E).T,M,atol=1e-15)
        bad=copy.deepcopy(block);bad['weight']=.5
        with self.assertRaises(ValueError):f.Game(self.lib,oracle.fixture(self.lib).nodes,[bad],169)
        with self.assertRaises(MemoryError):f.Game(self.lib,[dict(actor=0,children=[1,1],round=3),dict(actor=-1,children=[],round=3)],[],classes=100000)

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class FullstreetNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.lib=f.build(Path(cls.temp.name));cls.base=load_policy(os.environ['QUALIFICATION_BUILD'],f.old.ARTIFACT);cls.nodes=f.native_tree(cls.base.rules)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_all_three_street_tree_actions_and_cashflows_original_native(self):
        self.assertEqual(len(self.nodes),884);board=[4,9,14,19,24]
        for private in ([48,49,0,1],[0,1,48,49],[48,49,50,51]):
            ranks=[self.base.native.rank7(private[p:p+2]+board) for p in (0,2)];eq=(ranks[0]>ranks[1])+.5*(ranks[0]==ranks[1])
            def visit(k,prefix):
                node=self.nodes[k];s=self.base.native.NativeState(NativeGame([100,100]))
                for c in private:s.apply_action(c)
                def chance():
                    while s.is_chance_node() and not s.is_terminal():s.apply_action(board[len(s.audit()['board'])])
                for a in prefix:chance();self.assertIn(a,s.legal_actions());s.apply_action(a)
                chance()
                if node['actor']>=0:
                    self.assertEqual(s.current_player(),node['actor']);self.assertEqual(s.audit()['round'],node['round'])
                    for a,c in zip(node['native_actions'],node['children']):self.assertIn(a,s.legal_actions());visit(c,prefix+[a])
                else:
                    while not s.is_terminal():
                        chance()
                        if not s.is_terminal():s.apply_action(1)
                    self.assertAlmostEqual(s.returns()[0]/2,node['c0']+node['c1']*eq,places=12)
            visit(0,[])
    def test_physical_pair_equity_and_absolute_nuts_use_original_rank(self):
        board=[32,36,40,1,6];holes=(ctypes.c_int*(1081*2))();flags=(ctypes.c_int*1081)();eq=(ctypes.c_int8*(1081*1081))()
        self.assertEqual(self.lib.fs_world(model.ints(board),holes,flags,eq),1081)
        h=np.asarray(holes).reshape(1081,2);E=np.asarray(eq).reshape(1081,1081);self.assertEqual(int((E>=0).sum()),1070190)
        own=[44,48];self.assertEqual(self.lib.fs_nuts(model.ints(own),model.ints(board)),1)
        for i,j in ((0,1),(0,100),(100,900),(500,800),(1080,1000)):
            a=list(map(int,h[i]));b=list(map(int,h[j]))
            if set(a)&set(b):self.assertEqual(E[i,j],-1)
            else:
                ra=self.base.native.rank7(a+board);rb=self.base.native.rank7(b+board);self.assertEqual(E[i,j],2 if ra>rb else 1 if ra==rb else 0)
        for other in itertools.combinations([c for c in range(52) if c not in own+board],2):
            self.assertGreaterEqual(self.base.native.rank7(own+board),self.base.native.rank7(list(other)+board))
        for future in ([32,36,40,1,6],[32,36,40,2,7]):
            self.assertEqual(f.signal(self.lib,own,future)>>2,f.signal(self.lib,own,future[:3])>>2)
    def policy_fixture(self):
        # Test-only synthetic normalized arrays; no production/registry artifact.
        bases=[];size=0
        for n in self.nodes:
            bases.append(size if n['actor']>=0 else -1)
            if n['actor']>=0:size+=169*(1<<(2*n['round']))*len(n['children'])
        pi=np.zeros(size)
        for k,n in enumerate(self.nodes):
            if n['actor']>=0:
                na=len(n['children']);pi[bases[k]:bases[k]+169*(1<<(2*n['round']))*na]=1/na
        meta=dict(nodes=self.nodes,bases=bases,source_py_sha256=sha(Path(f.__file__)),source_cpp_sha256=sha(Path(f.__file__).with_name('fullstreet_core.cc')),binary_sha256=sha(Path(self.lib._name)),test_fixture=True)
        return f.Policy(meta,pi,np.zeros(size),self.lib,self.base)
    def test_source_guard_explicit_unlearned_and_short_allin_legal_response(self):
        q=self.policy_fixture();b=betting(self.base.rules);o=observe(b,(48,49),[])
        row=q.row(o);self.assertAlmostEqual(sum(row),1.);self.assertEqual(q.stats[0]['unlearned'],1)
        act(b,101);act(b,1);act(b,3);o=observe(b,(48,49),(4,9,14));row=q.row(o)
        self.assertEqual(sum(row),1.);self.assertEqual(row[o.actions.index(1)],1.);self.assertEqual(q.stats[1]['offtree'],1)
        bad=copy.deepcopy(q.meta);bad['binary_sha256']='0'*64
        with self.assertRaises(ValueError):f.Policy(bad,q.pi,q.average_mass,self.lib,self.base)
    def test_same_policy_bayes_range_with_exact_blockers(self):
        q=self.policy_fixture();b=betting(self.base.rules);act(b,8);o=observe(b,(48,49),[]);posterior=q.posterior(o)
        from gto.qualification.range_continuation import HOLES
        weights=[]
        for h in HOLES:
            if set(h)&set(o.own):weights.append(0.);continue
            past=observe(betting(self.base.rules),h,[]);weights.append(q._row(past,False)[past.actions.index(8)])
        np.testing.assert_allclose(posterior,np.array(weights)/sum(weights),atol=1e-15)
        self.assertAlmostEqual(sum(posterior),1.)

if __name__=='__main__':unittest.main()
