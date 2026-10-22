"""Offline review adapter: never an execution/scheduler authority."""
import importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'scripts/discover_review_queue.py'
def module():
 spec=importlib.util.spec_from_file_location('review_adapter',SOURCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class DiscoveryPreview(unittest.TestCase):
 def src(self,lane='A'):return {'lane':lane,'reference':'issue22','text':'- [ ] Reproduce boundary'}
 def cli(self,data):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'sources.json';p.write_text(data)
   return subprocess.run([sys.executable,'-B',str(SOURCE),'--sources',str(p)],text=True,capture_output=True,timeout=5)
 def test_deterministic_four_lane_dedup(self):
  m=module();a=m.preview([self.src(x) for x in 'ABCD']+[self.src()]);b=m.preview([self.src(x) for x in 'DCBA'])
  self.assertEqual(a,b);self.assertEqual(a['count'],4);self.assertFalse(a['executable']);self.assertEqual(a['version'],1)
  self.assertEqual(len({i['id'] for i in a['items']}),4)
 def test_invalid_outer_and_limit(self):
  m=module()
  for v in (None,{},'text',[self.src()]*101):
   with self.subTest(value=type(v).__name__),self.assertRaises(ValueError):m.preview(v)
 def test_invalid_rows_fail_closed(self):
  m=module()
  for v in (None,{},dict(self.src(),lane='X'),dict(self.src(),text=[]),dict(self.src(),reference=3)):
   with self.subTest(value=v),self.assertRaises(ValueError):m.preview([v])
 def test_untrusted_promotion_ignored(self):
  row=self.src();row.update(owner='injected',status='implemented',task={'execute':True},reviewed=True)
  i=module().preview([row])['items'][0];self.assertEqual(i['status'],'review_required');self.assertIsNone(i['owner']);self.assertNotIn('task',i)
 def test_existing_extractor_bounds_preserved(self):
  rows=[{'lane':'A','reference':'r'*400,'text':'\n'.join('- [ ] '+str(n)+'x'*300 for n in range(1100))}]
  r=module().preview(rows);self.assertEqual(r['count'],100);self.assertTrue(all(len(x['title'])==200 and len(x['reference'])==300 for x in r['items']))
 def test_preview_never_opens_state_or_dispatches(self):
  m=module()
  with patch('sqlite3.connect',side_effect=AssertionError('no state')),patch('subprocess.run',side_effect=AssertionError('no dispatch')):
   self.assertEqual(m.preview([])['count'],0);self.assertEqual(m.preview([self.src()])['count'],1)
 def test_cli_valid_output_only_json(self):
  r=self.cli(json.dumps([self.src()]));self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stderr,'');self.assertEqual(json.loads(r.stdout),module().preview([self.src()]))
 def test_cli_errors_do_not_echo_input(self):
  for s in ('SECRET_MARKER-not-json',json.dumps({'SECRET_MARKER':'not a list'})):
   r=self.cli(s);self.assertEqual(r.returncode,2);self.assertEqual(r.stdout,'');self.assertNotIn('SECRET_MARKER',r.stderr)
 def test_cli_bounded_regular_file_only(self):
  r=self.cli(' '*(1024*1024+1));self.assertEqual(r.returncode,2);self.assertEqual(r.stdout,'')
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'real';p.write_text('[]');link=Path(tmp)/'link';link.symlink_to(p)
   r=subprocess.run([sys.executable,'-B',str(SOURCE),'--sources',str(link)],text=True,capture_output=True,timeout=5);self.assertEqual(r.returncode,2);self.assertEqual(r.stdout,'')
