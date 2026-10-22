import base64
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zlib

from gto.native import verify_integration as verifier


class IntegrationInputSafety(unittest.TestCase):
    def check_payload(self, encoded, expected=b'owned'):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payloads = root / 'handoff/gto/compressed'
            payloads.mkdir(parents=True)
            (payloads / 'owned.zlib.b64').write_text(encoded)
            with patch.object(verifier, 'ROOT', root):
                return verifier.decoded_payload('owned', len(expected), hashlib.sha256(expected).hexdigest())

    def test_valid_owned_payload(self):
        encoded = base64.b64encode(zlib.compress(b'owned')).decode('ascii')
        self.assertEqual(self.check_payload(encoded), b'owned')

    def test_base64_is_strict(self):
        with self.assertRaises(ValueError):
            self.check_payload('@@@')

    def test_trailing_zlib_data_is_rejected(self):
        encoded = base64.b64encode(zlib.compress(b'owned') + b'trailing').decode('ascii')
        with self.assertRaises(ValueError):
            self.check_payload(encoded)

    def test_wrong_size_or_hash_is_rejected(self):
        for raw in (b'other', b'oversized'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.check_payload(base64.b64encode(zlib.compress(raw)).decode('ascii'))

    def test_unpinned_wheel_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / 'untrusted.whl'
            wheel.write_bytes(b'not a pinned wheel')
            destination = root / 'headers'
            with self.assertRaises(ValueError):
                verifier.extract_headers(wheel, destination)
            self.assertFalse(destination.exists())
