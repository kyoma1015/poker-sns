"""A fixed slow topology startup must finish before the cleanup timeout starts."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
@unittest.skipUnless(sys.platform=='linux','Linux process fixture required')
class TreeReadiness(unittest.TestCase):
 def test_startup_slower_than_runtime_timeout_is_not_cleanup_failure(self):
  with tempfile.TemporaryDirectory(prefix='owned-tree-qa-') as tmp:
   path=Path(tmp)/'ids.json';p=subprocess.Popen([sys.executable,'-B',str(ROOT/'tests/automation/owned_tree_probe.py'),str(path),'0','0.65'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
   try:
    out,err=p.communicate(timeout=6);self.assertEqual(p.returncode,0,err);data=json.loads(out)
    self.assertGreaterEqual(data['setup_seconds'],0.65)
    self.assertFalse(data['escaped_survived']);self.assertFalse(data['worker_liveness_unknown'])
    self.assertEqual(data['child_reaped_signal'],9);self.assertEqual(data['grand_reaped_signal'],9)
   finally:
    if p.poll() is None:os.killpg(p.pid,9)
    p.communicate(timeout=2)
if __name__=='__main__':unittest.main()
