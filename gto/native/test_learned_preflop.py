"""Native learning/evaluation integration, including deliberately unknown rows."""
from fractions import Fraction as F
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.training import NativeGame
from gto.native.preflop import decision
from gto.native.infoset_export import PolicySnapshot,report_json
from gto.native.joint_reach import joint_actions
from gto.native.learned_preflop import learned_report,learning_batch


class Learned(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR'])
        cls.native=importlib.import_module('pokerid_g12')

    def test_actual_trained_root_frequency_and_terminal_fold_ev_connected(self):
        game=NativeGame([4,4]);solver=self.native.Solver(game,.6,17,True,True,.1)
        for _ in range(200):solver.run_iteration()
        key=next(k for k in solver.keys() if json.loads(k)['seat']==0
            and not json.loads(k)['board'] and not json.loads(k)['betting_history']
            and solver.row(k)['updates']>0 and sum(solver.row(k)['average'])>0)
        hero=json.loads(key)['hand'];opponent=[c for c in range(52) if c not in hero][:2]
        policy=PolicySnapshot.from_solver(self.native,solver)
        r=learned_report(self.native,game,hero,[([opponent],F(1))],[],[0],policy,samples_per_deal=2)
        self.assertEqual(sum(r['target_policy'].values()),1)
        self.assertEqual(r['action_values'][0]['sample_mean_values'],[F(-1),F(1)])
        self.assertEqual(r['policy_digest'],policy.digest)
        self.assertFalse(r['equilibrium_verified'])

    def test_frozen_three_way_fourbet_report_repeats_exactly(self):
        game=NativeGame([200]*3);hero=[48,49];deals=[([[0,1],[4,5]],F(1))]
        prefix=[8,20,44];rows={}
        def recording(node):
            length=len(node.audit()['history']);selected=prefix[length] if length<len(prefix) else 1
            row={a:F(int(a==selected)) for a in node.legal_actions()}
            rows[node.information_state_string(node.current_player())]=row
            return row
        joint_actions(self.native,game,hero,deals,[],prefix,[0,1,92],recording,
            hero_seat=2,samples_per_deal=2,seed=17)
        target=decision(self.native,game,prefix,cards=[0,1,4,5,48,49]);recording(target)
        policy=PolicySnapshot(rows)
        args=(self.native,game,hero,deals,prefix,[0,1,92],policy)
        a=learned_report(*args,hero_seat=2,samples_per_deal=2,seed=17)
        b=learned_report(*args,hero_seat=2,samples_per_deal=2,seed=17)
        self.assertEqual(report_json(a),report_json(b))
        self.assertEqual(a['decision']['stage'],'vs_4bet')
        self.assertEqual(a['samples_completed'],6)
        self.assertIsNone(a['deviation']['global_exploitability'])
        self.assertFalse(a['deviation']['all_legal_actions_evaluated'])

    def test_missing_prefix_policy_is_unavailable_not_zero_ev(self):
        policy=PolicySnapshot({'unrelated':{0:F(1)}})
        r=learned_report(self.native,NativeGame([200]*3),[48,49],
            [([[0,1],[4,5]],F(1))],[8,20,44],[0],policy,hero_seat=2)
        self.assertIsNone(r['action_values'][0]);self.assertIsNone(r['target_policy'])
        self.assertEqual(r['action_status'][0],'prefix_policy_unobserved')

    def test_unknown_continuations_preserve_computed_fold_and_reserved_budget(self):
        game=NativeGame([4,4]);state=decision(self.native,game,[],cards=[48,49,0,1])
        policy=PolicySnapshot({state.information_state_string(0):{a:F(int(a==1)) for a in state.legal_actions()}})
        r=learned_report(self.native,game,[48,49],[([[0,1]],F(1))],[],[0,1,6],policy,samples_per_deal=2)
        self.assertEqual(r['samples_reserved'],6);self.assertEqual(r['samples_completed'],2)
        self.assertEqual(r['action_values'][0]['sample_mean_values'][0],-1)
        self.assertIsNone(r['action_values'][1]);self.assertIsNone(r['action_values'][6])
        self.assertEqual(r['deviation']['status'],'profile_action_values_missing')

    def test_stale_configuration_rejected_before_transport(self):
        game=NativeGame([4,4]);game.stacks[0]=8
        with self.assertRaisesRegex(ValueError,'configuration differs'):
            learned_report(self.native,game,[48,49],[([[0,1]],F(1))],[],[0],PolicySnapshot({'x':{0:F(1)}}))

    def test_finite_learning_batches_save_reproducible_policies_and_evaluate(self):
        query={'hero_cards':[48,49],'deals':[([[0,1]],F(1))],'history':[],
               'actions':[0],'samples_per_deal':1,'seed':17}
        with tempfile.TemporaryDirectory() as directory:
            paths=[Path(directory)/'a',Path(directory)/'b']
            results=[learning_batch(self.native,NativeGame([4,4]),[query],[2,4],p) for p in paths]
            self.assertEqual([x['policy_digest'] for x in results[0]['observations']],
                             [x['policy_digest'] for x in results[1]['observations']])
            self.assertEqual([x['queries'] for x in results[0]['observations']],
                             [x['queries'] for x in results[1]['observations']])
            self.assertTrue((paths[0]/'iteration-4.bin').is_file())
            self.assertFalse(results[0]['convergence_verified'])
            with self.assertRaises(FileExistsError):learning_batch(self.native,NativeGame([4,4]),[query],[2,4],paths[0])

    def test_bad_learning_schedule_rejected_without_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'new'
            with self.assertRaises(ValueError):learning_batch(self.native,NativeGame([4,4]),[{}],[4,2],path)
            self.assertFalse(path.exists())

    def test_cli_schedules_rfi_threebet_fourbet_without_claiming_convergence(self):
        import subprocess
        queries=[{'hero_cards':[48,49],'deals':[[[[0,1]],'1']],
            'hero_seat':seat,'history':history,'actions':[0],'samples_per_deal':1}
            for seat,history in ((0,[]),(0,[8,20]),(1,[8,20,44]))]
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'queries.json';source.write_text(json.dumps(queries))
            result=subprocess.run([sys.executable,'-B','-m','gto.native.learned_preflop',
                '--module-dir',os.environ['GTO_NATIVE_MODULE_DIR'],'--stacks','100','100',
                '--seed','17','--checkpoints','2','4','--queries',str(source),
                '--output',str(Path(directory)/'run')],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(result.stdout)
            self.assertEqual([r['decision']['stage'] for r in report['observations'][0]['queries']],
                ['rfi','vs_3bet','vs_4bet'])
            self.assertFalse(report['convergence_verified']);self.assertIsNone(report['global_exploitability'])


if __name__=='__main__':unittest.main()
