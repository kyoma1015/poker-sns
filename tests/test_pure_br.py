import itertools,tempfile,unittest
from pathlib import Path
from gto.abstract import pure_br as p,joint_update_audit as a,joint_stream as s,joint_history as h

class PureBRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.tmp=tempfile.TemporaryDirectory();cls.lib=p.build(Path(cls.tmp.name));cls.old=s.build(Path(cls.tmp.name)/'old')
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def extract(self):
        outs=[];post=[]
        for b,pi in enumerate(a.policies()):
            outs.append(a.native(self.lib,b,pi));post.append(self.lib.choices.copy())
        leaf=[sum(a.WEIGHT[b]*outs[b]['leaf'][i] for b in range(2)) for i in range(2*5*169)]
        nodes=[{'actor':0,'children':[1,2]},{'actor':-1},{'actor':1,'children':[3,4]},{'actor':-1},{'actor':-1}]
        pre,values=p.collapse_policy(leaf,nodes);pure=[]
        for b in range(2):
            pi=[0.]*16
            for k in (0,2,4,6):
                for typ in range(2):
                    i=a.BASE[k]+typ*2;choice=pre[k][typ] if k<4 else post[b][i];pi[i+choice]=1.
            pure.append(pi)
        return pure,values,outs
    def test_pure_policy_realized_value_equals_all64_policies_BR(self):
        pure,values,_=self.extract()
        for owner in (0,1):
            total=0.
            for b in range(2):
                hybrid=[pure[b][i] if h.OWNER(i)==owner else a.policies()[b][i] for i in range(16)]
                actual=a.native(self.old,b,hybrid)['ev'];total+=a.WEIGHT[b]*actual*(1 if owner==0 else -1)
            self.assertAlmostEqual(total,values[owner],delta=1e-12);self.assertAlmostEqual(total,a.brute_br(a.policies(),owner),delta=1e-12)
    def test_preflop_is_common_and_each_info_has_one_legal_action(self):
        pure,_,_=self.extract();self.assertEqual(pure[0][:8],pure[1][:8])
        for board in pure:
            for i in range(0,16,2):self.assertEqual(sorted(board[i:i+2]),[0.,1.])
    def test_performance_difference_uses_BR_own_reach_and_all_signed_terms(self):
        pure,values,outs=self.extract()
        for owner in (0,1):
            total=base=0.
            for b in range(2):
                own=pure[b].copy()
                for start in (8,10):
                    for action in range(2):own[start+action]*=pure[b][start-8+1]
                for start in (12,14):
                    for action in range(2):own[start+action]*=pure[b][4+start-12+1]
                total+=a.WEIGHT[b]*sum(own[i]*outs[b]['grad'][i] for i in range(16) if h.OWNER(i)==owner)
                base+=a.WEIGHT[b]*outs[b]['ev']*(1 if owner==0 else -1)
            self.assertAlmostEqual(total,values[owner]-base,delta=1e-12)
    def test_extractor_preserves_independent_value_outputs(self):
        for b,pi in enumerate(a.policies()):
            expected=a.native(self.old,b,pi);actual=a.native(self.lib,b,pi)
            for key in ('grad','avg','leaf','action_num','action_den'):
                for x,y in zip(expected[key],actual[key]):self.assertAlmostEqual(x,y,delta=1e-12)
    def test_illegal_choice_rejected(self):
        with self.assertRaises(ValueError):p.pure_policy(b'\xff',b'',1)
    def test_future_board_clairvoyance_is_strictly_stronger_than_legal_preflop(self):
        nodes=[{'actor':0,'children':[1,2]},{'actor':-1},{'actor':-1}];boards=[]
        # One hand; continue pays +1/-1 on equiprobable FUTURE boards,fold pays0.
        # BB has no action; its leaf includes fixed SB continue probability.5.
        for payoff in (1.,-1.):
            leaf=[0.]*(2*3*169);leaf[2*169]=payoff;leaf[(3+2)*169]=-.5*payoff;boards.append(leaf)
        mean=[.5*(x+y) for x,y in zip(*boards)];choices,legal=p.collapse_policy(mean,nodes)
        illegal=sum(.5*p.collapse_policy(b,nodes)[1][0] for b in boards)
        self.assertEqual(choices[0][0],0);self.assertEqual(legal[0],0.);self.assertEqual(illegal,.5)
    def test_snapshot_never_writes_source(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'frozen';rows=[{'representative':[0,4,8],'multiplicity':1}];writer=s.Store(path,rows)
            with writer.db:writer.put('baseline:ready',b'1')
            writer.db.close();source=p.Frozen(path,rows);before=source.numeric_digest()
            with self.assertRaises(sqlite3.OperationalError):source.db.execute("update state set value='bad' where key='pre'")
            self.assertEqual(before,source.numeric_digest());source.close()
if __name__=='__main__':unittest.main()
