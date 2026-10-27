import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('startup_diagnostic', 'scripts/video_ci_startup_diagnostic.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class StartupDiagnosticTests(unittest.TestCase):
    def test_known_failure_categories(self):
        for text,label in [
            ('toomanyrequests: pull rate limit','REGISTRY_RATE_LIMIT'),
            ('failed to authorize: failed to fetch oauth token','REGISTRY_AUTH_FAILURE'),
            ('failed to resolve reference docker.io/example','REGISTRY_FETCH_FAILURE'),
            ('port is already allocated','LOCAL_PORT_CONFLICT'),
            ('container unhealthy','CONTAINER_HEALTH_FAILURE'),
            ('read: connection reset by peer','NETWORK_FAILURE'),
        ]:
            with self.subTest(label=label): self.assertEqual(m.classify_startup(text),label)

    def test_unknown_log_remains_opaque(self):
        self.assertEqual(m.classify_startup('Secret Key: NEVER_OUTPUT_THIS'),'UNCLASSIFIED_STARTUP_FAILURE')

    def test_cli_never_echoes_credentials_even_on_recognized_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'startup.log'
            path.write_text('Secret Key: NEVER_OUTPUT_THIS\nfailed to fetch oauth token https://secret.invalid/')
            result=subprocess.run([sys.executable,'scripts/video_ci_startup_diagnostic.py',str(path)],capture_output=True,text=True,check=True)
            self.assertEqual(result.stdout,'Isolated startup diagnostic: REGISTRY_AUTH_FAILURE\n')
            self.assertEqual(result.stderr,'')

    def test_unavailable_and_oversized_logs_are_fixed_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'startup.log'
            result=subprocess.check_output([sys.executable,'scripts/video_ci_startup_diagnostic.py',str(path)],text=True)
            self.assertIn('STARTUP_LOG_UNAVAILABLE',result)
            path.write_bytes(b'x'*(2*1024*1024+1))
            result=subprocess.check_output([sys.executable,'scripts/video_ci_startup_diagnostic.py',str(path)],text=True)
            self.assertEqual(result,'Isolated startup diagnostic: STARTUP_LOG_TOO_LARGE\n')

if __name__ == '__main__': unittest.main()
