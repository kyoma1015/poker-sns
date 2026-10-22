import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class PreviewUnicode(unittest.TestCase):
    def check(self, field, value):
        source = {'lane': 'A', 'reference': 'review', 'text': '- [ ] safe title'}
        source[field] = '- [ ] ' + value if field == 'text' else value
        with tempfile.TemporaryDirectory(prefix='pokerid-unicode-') as folder:
            path = Path(folder) / 'sources.json'
            path.write_text(json.dumps([source]), encoding='utf-8')
            env = {**os.environ, 'PYTHONIOENCODING': 'utf-8:strict'}
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/discover_review_queue.py'),
                                     '--sources', str(path)], capture_output=True, env=env, timeout=10)
        # Preserve the existing two safe CLI outcomes: complete JSON or a
        # sanitized validation rejection. Never emit partial output/traceback.
        self.assertIn(result.returncode, (0, 2), result.stderr.decode('utf-8', errors='replace'))
        if result.returncode == 2:
            self.assertEqual(result.stdout, b'')
            self.assertEqual(result.stderr, b'review queue preview input rejected\n')
        else:
            self.assertEqual(result.stderr, b'')
            data = json.loads(result.stdout.decode('utf-8'))
            self.assertFalse(data['executable'])
            self.assertEqual(data['count'], 1)
            self.assertEqual(data['items'][0]['reference' if field == 'reference' else 'title'], value)

    def test_high_surrogate_reference(self): self.check('reference', '\ud800')
    def test_low_surrogate_reference(self): self.check('reference', '\udfff')
    def test_high_surrogate_title(self): self.check('text', '\ud800')
    def test_low_surrogate_title(self): self.check('text', '\udfff')
    def test_normal_japanese(self): self.check('text', '品質確認')
