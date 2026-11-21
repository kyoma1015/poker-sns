import copy, json, tempfile, unittest
from pathlib import Path
from gto.abstract import matched_history as m, joint_reach as j, joint_stream as s, joint_vector as v

class MatchedHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); root=Path(cls.tmp.name)
        cls.lib=v.build(root/'vector')
        cls.reference=j.build(root/'reference')
        # Small explicit non-poker cashflows for unit math only; measured run uses
        # exact real-card worlds in result.json, not these synthetic equities.
        cls.ws=[{'signals':[h*8,vv*8],'flop':b,'mass':1/8,'equity':e}
            for b in ([0,5,10],[1,6,11]) for h,vv,e in ((0,2,.2),(0,3,.35),(1,2,.65),(1,3,.8))]
        cls.g=j.prepare(s.layout(4)[0],cls.ws); cls.kernel=m.Kernel(cls.lib,cls.g)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_actual_limp_fourbet_node_and_no_future_board_in_preflop_key(self):
        nodes=self.g['nodes']; node=next(k for k,n in enumerate(nodes) if n.get('history')==['call','raise_to_5','raise_to_18','raise_to_42'])
        self.assertEqual(nodes[node]['actions'],['fold','call','raise_to_100'])
        self.assertTrue(all(len(key)==1 for k,key,i in self.g['keys'] if nodes[k]['street']=='preflop'))
    def test_every_vector_regret_and_average_cell_matches_path_products(self):
        pi=m.policy(self.g,[float(i%11) for i in range(len(self.g['width']))])
        a=self.kernel(pi); b=m.python_oracle(self.g,pi)
        for field in ('grad','avg'):
            self.assertLess(max(abs(x-y) for x,y in zip(a[field],b[field])),1e-10)
        self.assertAlmostEqual(a['ev'],b['ev'],delta=1e-10)
    def test_vanilla_updates_equal_existing_independent_world_CFR(self):
        expected=j.Solver(self.reference,self.g);actual=m.Trainer(self.g,self.kernel)
        expected.run(3)
        for _ in range(3):actual.step('vanilla')
        for a,b in ((actual.R,expected.regret),(actual.S,expected.sums)):
            self.assertLess(max(abs(x-y) for x,y in zip(a,b)),1e-10)
    def test_all_three_updates_match_independent_python_and_resume(self):
        teacher=m.Trainer(self.g,self.kernel)
        for _ in range(4):teacher.step('cfr_plus')
        state=teacher.state()
        for method in m.METHODS:
            native=m.Trainer(self.g,self.kernel); py=m.Trainer(self.g,lambda pi:m.python_oracle(self.g,pi))
            native.restore(state);py.restore(state)
            for _ in range(3):native.step(method);py.step(method)
            for field in ('R','S'):
                self.assertLess(max(abs(x-y) for x,y in zip(native.state()[field],py.state()[field])),1e-9)
            with tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/'checkpoint.json';m.checkpoint(path,native,'game-id',method)
                recovered=m.Trainer(self.g,self.kernel);m.resume(path,recovered,'game-id',method)
                self.assertEqual(native.state(),recovered.state())
                native.step(method);recovered.step(method);self.assertEqual(native.state(),recovered.state())
                before=recovered.state()
                with self.assertRaises(ValueError):m.resume(path,recovered,'other-game',method)
                self.assertEqual(before,recovered.state())
    def test_legal_pure_responses_equal_existing_independent_BR_and_realized_payoff(self):
        pi=m.policy(self.g,[float(i%7) for i in range(len(self.g['width']))])
        for owner in (0,1):
            pure,value=m.pure_response(self.g,pi,owner)
            self.assertAlmostEqual(value,j.independent_br(self.g,pi,owner),delta=1e-10)
            self.assertAlmostEqual(value,m.python_oracle(self.g,pure)['ev']*(1 if owner==0 else -1),delta=1e-10)
            for k,key,i in self.g['keys']:
                if self.g['nodes'][k]['actor']==owner:
                    row=pure[i:i+len(self.g['nodes'][k]['children'])]
                    self.assertEqual(sum(row),1);self.assertTrue(all(x in (0,1) for x in row))
    def test_resume_rejects_corrupt_average_without_changing_state(self):
        x=m.Trainer(self.g,self.kernel)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'x';m.checkpoint(path,x,'id','cfr_plus');data=json.loads(path.read_text());data['S'][0]=-1;path.write_text(json.dumps(data))
            before=x.state()
            with self.assertRaises(ValueError):m.resume(path,x,'id','cfr_plus')
            self.assertEqual(before,x.state())


class FrozenProjectionTests(unittest.TestCase):
    def test_projection_matches_existing_immutable_frozen_lift(self):
        from unittest.mock import patch
        from gto.abstract import matched_frozen as f, joint_stream_study as study
        root=Path('docs/qa/matched-history-20261116')
        result=json.loads((root/'results.json').read_text());worlds=result['worlds']
        g=j.prepare(s.layout(4)[0],worlds);actual=f.lift(g)
        boards=sorted({tuple(w['flop']) for w in worlds})
        rows=[{'representative':list(board),'multiplicity':1} for board in boards]
        codes={}
        for board in boards:
            by_class={}
            for w in worlds:
                if tuple(w['flop'])!=board:continue
                for owner in (0,1):
                    flag=f.fs.groups({'pairs':[w['holes'][owner]],'flop':list(board)})[0]
                    by_class[w['signals'][owner]//8]=w['signals'][owner]//8*8+flag
            codes[board]=sorted(by_class.values())
        with tempfile.TemporaryDirectory() as folder:
            store=s.Store(Path(folder)/'frozen.sqlite',rows)
            try:
                with patch.object(study.c,'read',lambda directory,row:({'codes':codes[tuple(row['representative'])]},[])):
                    self.assertTrue(study.frozen(store,'unused'))
                policies={board:s.strategy(*store.state(bi,len(codes[board])),s.layout(len(codes[board]))[2],True) for bi,board in enumerate(boards)}
                for k,key,i in g['keys']:
                    n=g['nodes'][k];count=len(n['children']);board=boards[0] if n['street']=='preflop' else key[0]
                    if n['street']=='preflop':typ=key[0]
                    else:typ=next(t for t,code in enumerate(codes[board]) if code//8==key[1]//8)
                    at=s.layout(len(codes[board]))[1][k]+typ*count
                    self.assertEqual(actual[i:i+count],policies[board][at:at+count])
            finally:store.db.close()


class MeasuredCheckpointTests(unittest.TestCase):
    def test_all_twelve_actual_checkpoints_reproduce_reported_final_metrics(self):
        root=Path('docs/qa/matched-history-20261116');result=json.loads((root/'results.json').read_text())
        for case in result['cases']:
            ws=copy.deepcopy(result['worlds']);boards=sorted({tuple(w['flop']) for w in ws})
            for w in ws:w['mass']=case['board_weights'][boards.index(tuple(w['flop']))]/4
            g=j.prepare(s.layout(4)[0],ws);self.assertEqual(m.identity(g),case['identity'])
            for method,points in case['methods'].items():
                x=m.Trainer(g,lambda pi:m.python_oracle(g,pi))
                path=root/'checkpoints'/f"{case['board_weights'][0]}-{case['teacher_iterations']}-{method}.json"
                m.resume(path,x,m.identity(g),method)
                self.assertEqual(x.t,case['teacher_iterations']+128)
                metric=m.measure(g,x.average())
                for key,value in metric.items():self.assertAlmostEqual(value,points[-1][key],delta=1e-10)

if __name__=='__main__':unittest.main()
