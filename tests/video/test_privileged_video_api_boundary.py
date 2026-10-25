"""Fail-closed source boundary: privileged key may call narrowly scoped RPCs only.

This is a defense-in-depth check, NOT proof that Supabase's global
service_role credential cannot call the Storage admin API externally.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [ROOT / 'api/video-finalize.ts', ROOT / 'api/video-production-supabase-adapters.ts', ROOT / 'api/video-media.ts']

class PrivilegedVideoApiBoundary(unittest.TestCase):
    def test_no_privileged_storage_mutations(self):
        for path in SOURCES:
            text = path.read_text()
            self.assertNotRegex(text, r'(?s)admin\\.storage\\.from\\([^)]*\\)\\s*\\.\\s*(?:upload|update|remove|move|copy|createSignedUploadUrl)\\s*\\(', str(path))
            self.assertNotRegex(text, r'(?s)admin\\.storage\\.\\w+\\s*\\(', str(path))
            self.assertNotRegex(text, r'/storage/v1/(?:object|bucket)/(?:upload|move|copy|remove|delete)', str(path))
    def test_privileged_rpc_allowlist(self):
        allowed = {'video_reserve_object_key', 'video_production_storage_generation',
                   'video_production_publish_fenced', 'video_production_reconcile_fenced'}
        for path in SOURCES:
            text = path.read_text()
            used = set(re.findall(r'admin\\.rpc\\(\\s*[\\x27\\x22]([^\\x27\\x22]+)', text))
            self.assertLessEqual(used, allowed, f'{path}: privileged RPC outside allowlist: {used-allowed}')

if __name__ == '__main__':
    unittest.main()
