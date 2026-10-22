"""Immutable resource-limit regression; only owned synthetic checkpoint bytes."""
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from gto.native.checkpoints import load_verified_checkpoint, verified_snapshot


def checkpoint():
    def uint(value): return struct.pack('<Q', value)
    def text(value):
        raw = value.encode()
        return uint(len(raw)) + raw
    raw = (b'PIDG12S1' + text('fixture') + b''.join(uint(1) for _ in range(5))
           + struct.pack('<d', .1) + uint(3) + uint(9) + struct.pack('<d', .6)
           + text('synthetic RNG, not native-valid') + uint(0))
    return raw + hashlib.sha256(raw).digest()


class CheckpointBudget(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.source = Path(self.directory.name) / 'synthetic.bin'
        self.original = checkpoint()
        self.source.write_bytes(self.original)

    def tearDown(self):
        self.directory.cleanup()

    def rejects_before_any_file_open(self, value):
        # Even an existing valid file must not be read or a temp snapshot opened.
        with patch.object(Path, 'open', side_effect=AssertionError('opened before budget validation')):
            with self.assertRaises(ValueError):
                with verified_snapshot(self.source, 'fixture', max_bytes=value):
                    self.fail('invalid budget was accepted')

    def test_nonfinite_limit_is_rejected_before_io(self):
        for value in (float('nan'), float('inf'), float('-inf')):
            with self.subTest(value=value):
                self.rejects_before_any_file_open(value)

    def test_noninteger_limit_is_rejected_before_io(self):
        for value in (True, False, 1., float(len(self.original)), '1000', None, object()):
            with self.subTest(value=repr(value)):
                self.rejects_before_any_file_open(value)

    def test_nonpositive_integer_limit_is_rejected_before_io(self):
        for value in (0, -1, -1000):
            with self.subTest(value=value):
                self.rejects_before_any_file_open(value)

    def test_exact_positive_limit_accepts_owned_snapshot(self):
        with verified_snapshot(self.source, 'fixture', max_bytes=len(self.original)) as (copy, metadata):
            self.assertNotEqual(copy, self.source)
            self.assertEqual(copy.read_bytes(), self.original)
            self.assertEqual(metadata['bytes'], len(self.original))
        self.assertFalse(copy.exists())
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_limit_one_byte_smaller_rejects_before_native(self):
        class NeverLoad:
            def load_binary(self, path, contract):
                raise AssertionError('oversized input reached native')
        with self.assertRaisesRegex(ValueError, 'size limit'):
            load_verified_checkpoint(NeverLoad(), self.source, 'fixture', max_bytes=len(self.original)-1)
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_nan_and_inf_never_reach_native(self):
        class NeverLoad:
            def load_binary(self, path, contract):
                raise AssertionError('invalid budget reached native')
        for value in (float('nan'), float('inf')):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    load_verified_checkpoint(NeverLoad(), self.source, 'fixture', max_bytes=value)

    def test_native_gets_verified_copy_only_for_valid_limit(self):
        original = self.source
        expected = self.original
        class VerifyCopy:
            def load_binary(self, path, contract):
                assert Path(path) != original
                assert Path(path).read_bytes() == expected
                assert contract == 'fixture'
        result = load_verified_checkpoint(VerifyCopy(), self.source, 'fixture', max_bytes=len(expected))
        self.assertEqual(result['bytes'], len(expected))
        self.assertEqual(original.read_bytes(), expected)


if __name__ == '__main__':
    unittest.main()
