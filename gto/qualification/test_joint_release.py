"""Independent exact BR/CF reach and original native legality/settlement."""
import copy,gzip,json,os,tempfile,unittest
from pathlib import Path
import numpy as np
from gto.abstract import joint_vector,joint_history,joint_update_audit as toy,joint_reach,model
from gto.qualification import joint_release as j
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.native_mccfr import betting
from gto.qualification.policy import act,sha
from gto.qualification.range_continuation import history_action
from gto.native.training import NativeGame


def fixture(lib):
    nodes=[dict(actor=a,children=c,street='flop' if k>=4 else 'preflop',c0=toy.C0[k],c1=toy.C1[k]) for k,(a,c) in enumerate(zip(toy.ACTOR,toy.CHILD))]
    pre=[dict(actor=0,children=[1,2]),dict(actor=-1,children=[]),dict(actor=1,children=[3,4]),dict(actor=-1,children=[]),dict(actor=-1,children=[])]
    bs=[dict(mass=np.asarray(toy.MASSES[b]).reshape(2,2).tolist(),equity=np.asarray(toy.EQUITY[b]).reshape(2,2).tolist()) for b in range(2)]
    return j.Trainer(lib,nodes,pre,[-1,1,-1,3,4,-1,-1,-1,-1],bs,toy.WEIGHT,2,2)

class JointOracles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.temp=tempfile.TemporaryDirectory();cls.lib=joint_vector.build(Path(cls.temp.name))
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_gradients_average_and_current_reach_match_path_oracle(self):
        q=fixture(self.lib)
        for _ in range(13):q.step()
        for b in range(2):
            pi=q.policy(b,False);a=q.block(b,pi);o=toy.oracle(b,pi)
            for field,expected in [('grad','grad'),('avg','avg'),('num','action_num'),('den','action_den')]:np.testing.assert_allclose(a[field],o[expected],atol=2e-12)
            self.assertAlmostEqual(a['metric'][0],o['ev'],places=12)
    def test_schedule_and_resume_match_independent_joint_teacher(self):
        q=fixture(self.lib);teacher=joint_history.Trainer([[.5]*16 for _ in range(2)])
        for _ in range(32):q.step();teacher.step('alternating')
        for b in range(2):
            np.testing.assert_allclose(q.policy(b,True),teacher.average()[b],atol=2e-12)
            np.testing.assert_allclose(q.R,teacher.R[b][:8],atol=2e-12)
            np.testing.assert_allclose(q.posts[b][0],teacher.R[b][8:],atol=2e-12)
        other=fixture(self.lib);other.restore(q.state());q.step();other.step();self.assertEqual(q.state(),other.state())
    def test_bayes_and_future_board_hidden_at_preflop(self):
        q=fixture(self.lib)
        for _ in range(16):q.step()
        boards=[(0,5,10),(12,17,22)];ws=[]
        for b in range(2):
            for h in range(2):
                for v in range(2):
                    m=toy.MASSES[b][2*h+v]*toy.WEIGHT[b]
                    if m:ws.append(dict(signals=(h*8,v*8),flop=boards[b],mass=m,equity=toy.EQUITY[b][2*h+v]))
        g=joint_reach.prepare(q.nodes,ws);pi=[0.]*len(g['width'])
        for k,key,start in g['keys']:
            b=0 if q.nodes[k]['street']=='preflop' else boards.index(key[0]);h=key[0] if q.nodes[k]['street']=='preflop' else key[1]//8;i=toy.BASE[k]+2*h;pi[start:start+2]=q.policy(b,True)[i:i+2]
        for b in range(2):
            np.testing.assert_array_equal(q.policy(b,True)[:q.P],q.policy(0,True)[:q.P])
            h=1;got=joint_reach.conditional_opponent(g,pi,4,(boards[b],h*8))
            p=q.policy(b,True);weights=np.array(toy.MASSES[b][2*h:2*h+2])*[p[5],p[7]];weights/=weights.sum()
            np.testing.assert_allclose(got['opponent_class_probability'][:2],weights,atol=1e-12)
    def test_nonnegative_lattice_statistical_lower_bound(self):
        from gto.qualification.joint_river_bound import cdf_lower
        self.assertEqual(cdf_lower([0.]*32)[0],0)
        lower,_=cdf_lower([2.]*64)
        self.assertGreater(lower,0);self.assertLess(lower,2)
        with self.assertRaises(ValueError):cdf_lower([-.5,0.])

    def test_exact_convergence_against_all64_pure_policies(self):
        out=Path(self.temp.name)/'tiny.json';self.assertTrue(j.tiny(self.lib,out));d=json.loads(out.read_text())
        self.assertTrue(all(g['curve'][-1]['NC_bb']<.0001 for g in d['games']))

@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD') and os.environ.get('RANGE_BUILD'),'native/rank builds required')
class NativeOracle(unittest.TestCase):
    def test_all_tree_actions_and_cashflows_with_original_native(self):
        base=load_policy(os.environ['QUALIFICATION_BUILD'],j.ARTIFACT);nodes,pre,bound=j.native_tree(base.rules);private=[48,49,0,1];board=[4,9,14,19,24];eq=(base.native.rank7(private[:2]+board)>base.native.rank7(private[2:]+board))+.5*(base.native.rank7(private[:2]+board)==base.native.rank7(private[2:]+board))
        def visit(k,prefix):
            n=nodes[k];s=base.native.NativeState(NativeGame([100,100]))
            for c in private:s.apply_action(c)
            def chance():
                while s.is_chance_node() and not s.is_terminal():s.apply_action(board[len(s.audit()['board'])])
            for a in prefix:chance();self.assertIn(a,s.legal_actions());s.apply_action(a)
            chance()
            if n['actor']>=0:
                self.assertEqual(s.current_player(),n['actor'])
                for a,c in zip(n['native_actions'],n['children']):self.assertIn(a,s.legal_actions());visit(c,prefix+[a])
            else:
                while not s.is_terminal():
                    chance()
                    if not s.is_terminal():s.apply_action(1)
                self.assertAlmostEqual(s.returns()[0]/2,n.get('c0',0)+n.get('c1',0)*eq,places=12)
        visit(0,[])
        for private in ([0,1,48,49],[48,49,50,51]):
            eq=(base.native.rank7(private[:2]+board)>base.native.rank7(private[2:]+board))+.5*(base.native.rank7(private[:2]+board)==base.native.rank7(private[2:]+board));visit(0,[])
    def test_absolute_nuts_jam_dominates_check_for_all990_opponents(self):
        import itertools
        from gto.qualification.release_deviation import nuts
        base=load_policy(os.environ['QUALIFICATION_BUILD'],j.ARTIFACT);own=[44,48];board=[32,36,40,1,6]
        self.assertTrue(nuts(base.native,own,board));opponents=list(itertools.combinations([x for x in range(52) if x not in own+board],2));self.assertEqual(len(opponents),990)
        for other in opponents:
            scores=[]
            for jam in (False,True):
                s=base.native.NativeState(NativeGame([100,100]))
                for c in list(other)+own:s.apply_action(c)
                def chance():
                    while s.is_chance_node() and not s.is_terminal():s.apply_action(board[len(s.audit()['board'])])
                for a in (8,1,1,1,1,1):chance();s.apply_action(a)
                chance();self.assertEqual(s.audit()['round'],3);self.assertEqual(s.current_player(),1)
                s.apply_action(max(s.legal_actions()) if jam else 1);s.apply_action(1);self.assertTrue(s.is_terminal());scores.append(s.returns()[1]/2)
            self.assertEqual(scores[1]-scores[0],47)

    def test_conditional990_runouts_and_blockers_match_original_rank(self):
        from gto.abstract import flop_exact
        base=load_policy(os.environ['QUALIFICATION_BUILD'],j.ARTIFACT)
        with tempfile.TemporaryDirectory() as directory:
            lib=flop_exact.build(Path(directory));flop=[0,5,10];holes=[(48,49),(44,45),(48,50)];m=flop_exact.matrix(lib,flop,holes)
            available=[x for x in range(52) if x not in list(holes[0]+holes[1])+flop];wins=ties=0
            import itertools
            for run in itertools.combinations(available,2):
                a=base.native.rank7(list(holes[0])+flop+list(run));b=base.native.rank7(list(holes[1])+flop+list(run));wins+=a>b;ties+=a==b
            self.assertEqual(m['win'][1],wins);self.assertEqual(m['tie'][1],ties)
            self.assertEqual(m['win'][2],0);self.assertEqual(m['tie'][2],0)
            from gto.qualification.policy import hand
            self.assertEqual(m['labels'],[hand(h) for h in holes])

    def test_same_digest_guard_and_short_allin_legal_response(self):
        from gto.qualification.public_response import observe
        base=load_policy(os.environ['QUALIFICATION_BUILD'],j.ARTIFACT);rank=model.load(Path(os.environ['RANGE_BUILD'])/'range.so')
        d=json.loads(gzip.decompress(Path('docs/qa/joint-release-20261119/17119201/policy-final.json.gz').read_bytes()));d=copy.deepcopy(d);d.pop('policy_digest');d['identity']['rank_binary_sha256']=sha(Path(rank._name));d['identity']['source_sha256']=sha(Path(j.__file__));d['identity']['test_fixture']=True;q=j.JointPolicy(d,base,rank)
        b=betting(base.rules);act(b,101);act(b,1);act(b,3)
        o=observe(b,(48,49),(4,9,14));r=q.row(o,True);self.assertEqual(sum(r),1);self.assertEqual(r[o.actions.index(1)],1)
        bad=copy.deepcopy(d);bad['identity']['rank_binary_sha256']='0'*64
        with self.assertRaises(ValueError):j.JointPolicy(bad,base,rank)

if __name__=='__main__':unittest.main()
