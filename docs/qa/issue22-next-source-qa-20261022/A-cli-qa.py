"""Isolated no-state CLI regression QA. Pass the pinned A109 checkout root."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(sys.argv.pop(1)).resolve()


class ReadOnlyPreviewQA(unittest.TestCase):
    def check(self, raw, expected):
        with tempfile.TemporaryDirectory(prefix='pokerid-preview-qa-') as directory:
            path = Path(directory) / 'input.json'
            path.write_bytes(raw)
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/discover_review_queue.py'),
                                     '--sources', str(path)], capture_output=True, timeout=10)
        self.assertEqual(result.returncode, expected)
        if expected == 2:
            self.assertEqual(result.stdout, b'')
            self.assertEqual(result.stderr, b'review queue preview input rejected\n')
        else:
            self.assertEqual(result.stderr, b'')
            parsed = json.loads(result.stdout)
            self.assertFalse(parsed['executable'])
            self.assertEqual(parsed['items'][0]['title'], '品質確認')

    def test_deep_json(self): self.check(b'[' * 2000 + b'0' + b']' * 2000, 2)
    def test_oversized_integer(self): self.check(b'[' + b'9' * 5000 + b']', 2)
    def test_invalid_utf8(self): self.check(b'\xff', 2)
    def test_null(self): self.check(b'null', 2)
    def test_boolean_lane(self):
        self.check(json.dumps([{'lane': True, 'reference': 'synthetic', 'text': '- [ ] title'}]).encode(), 2)
    def test_japanese(self):
        self.check(json.dumps([{'lane': 'A', 'reference': 'synthetic', 'text': '- [ ] 品質確認'}]).encode(), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
