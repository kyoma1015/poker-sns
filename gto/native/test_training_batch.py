"""Actual reconstructed native training lifecycle; never historical checkpoints."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from gto.native.training import NativeGame, checkpoint, train_batch, contract_for


class NativeTraining(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.environ['GTO_NATIVE_MODULE_DIR'])
        cls.native = importlib.import_module('pokerid_g12')

    def solver(self, players=2):
        g = NativeGame([4] * players, bb=2, bba=2, rake_num=0, rake_den=1)
        return g, self.native.Solver(g, .6, 17, True, True, .1)

    def test_split_resume_equals_uninterrupted(self):
        game, direct = self.solver()
        _, split = self.solver()
        with tempfile.TemporaryDirectory() as d:
            a, b, out = [Path(d)/p for p in ('a.bin','b.bin','policies.jsonl')]
            train_batch(direct, game, 6, a)
            train_batch(split, game, 3, b)
            _, recovered = self.solver()
            result = train_batch(recovered, game, 3, Path(d)/'c.bin', resume=b, export=out)
            self.assertEqual(recovered.iteration, 6)
            self.assertEqual(recovered.rng_state(), direct.rng_state())
            self.assertEqual({k:recovered.row(k) for k in recovered.keys()}, {k:direct.row(k) for k in direct.keys()})
            self.assertEqual(a.read_bytes(), (Path(d)/'c.bin').read_bytes())
            self.assertEqual(result['iterations_completed'], 3)
            self.assertGreater(result['infosets'], 0)
            self.assertTrue(out.stat().st_size > 0)
            for line in out.read_text().splitlines():
                self.assertIsNone(json.loads(line)['ev'])

    def test_all_player_counts_use_native_engine(self):
        with tempfile.TemporaryDirectory() as d:
            for n in range(2,10):
                with self.subTest(players=n):
                    g,s = self.solver(n)
                    r = train_batch(s,g,2,Path(d)/f'{n}.bin')
                    self.assertTrue(r['native_engine'])
                    self.assertEqual(r['iteration'], 2)

    def test_corrupt_resume_refused_before_training(self):
        with tempfile.TemporaryDirectory() as d:
            g,s = self.solver(); p=Path(d)/'a.bin'
            train_batch(s,g,1,p)
            data=bytearray(p.read_bytes()); data[-1] ^= 1; p.write_bytes(data)
            _,fresh=self.solver()
            with self.assertRaises(ValueError): train_batch(fresh,g,1,Path(d)/'b.bin',resume=p)
            self.assertEqual(fresh.iteration,0)

    def test_contract_binds_stacks_and_rules(self):
        g,_=self.solver()
        other=NativeGame([6,4],bb=2,bba=2,rake_num=0,rake_den=1)
        self.assertNotEqual(contract_for(g),contract_for(other))
        with tempfile.TemporaryDirectory() as d:
            _,s=self.solver(); p=Path(d)/'a.bin'; train_batch(s,g,1,p)
            mismatch=self.native.Solver(other,.6,17,True,True,.1)
            with self.assertRaises(ValueError): train_batch(mismatch,other,1,Path(d)/'b.bin',resume=p)

    def test_existing_destination_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            g,s=self.solver(); p=Path(d)/'existing'; p.write_bytes(b'original')
            with self.assertRaises(FileExistsError): train_batch(s,g,1,p)
            self.assertEqual(p.read_bytes(), b'original')
            self.assertEqual(s.iteration,0)

    def test_publish_failure_leaves_no_partial_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            g,s=self.solver(); s.run_iteration(); p=Path(d)/'out.bin'
            with patch('gto.native.training.os.link',side_effect=OSError('fixture publish failure')):
                with self.assertRaises(OSError): checkpoint(s,p,contract_for(g))
            self.assertFalse(p.exists())
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_stop_saves_completed_iteration_only(self):
        with tempfile.TemporaryDirectory() as d:
            g,s=self.solver(); calls=[]
            def stop(): calls.append(1); return s.iteration>=2
            p=Path(d)/'stopped.bin'; result=train_batch(s,g,5,p,stop_check=stop)
            self.assertEqual(result['iterations_completed'],2)
            self.assertTrue(result['stopped'])
            _,fresh=self.solver(); train_batch(fresh,g,1,Path(d)/'resumed.bin',resume=p)
            self.assertEqual(fresh.iteration,3)

    def test_finite_budget_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as d:
            for count in (True,0,-1,1.5,100001):
                g,s=self.solver()
                with self.assertRaises(ValueError): train_batch(s,g,count,Path(d)/'out')
                self.assertEqual(s.iteration,0)

if __name__=='__main__': unittest.main()
