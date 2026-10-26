import copy,importlib,json,os,subprocess,sys,unittest
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.action_report import consume_report,render_html
from gto.native.infoset_export import export_action_classes,report_json
from gto.native import test_infoset_export as fixtures

class Consumer(unittest.TestCase):
 @classmethod
 def setUpClass(cls):fixtures.Export.setUpClass()
 def setUp(self):
  t=fixtures.Export();t.setUp();self.report=export_action_classes([t.record()]);self.raw=report_json(self.report)
  self.expected={k:self.report[k] for k in ('observation_digest','config_digest','policy_digest')}
 def consume(self,report=None):return consume_report(report_json(report) if report is not None else self.raw,expected=self.expected)
 def test_native_producer_consumer_exact_partial(self):
  out=self.consume();hand=next(r for r in out['hands'] if r['observed_combinations']);self.assertEqual(hand['observed_action_values'],['1','2'])
  self.assertIsNone(hand['complete_class_action_values']);self.assertIsNone(hand['frequencies']);self.assertIsNone(out['hand169_ev']);self.assertIn('PARTIAL_COVERAGE',out['warnings'])
 def test_wrong_pin_refuses(self):
  pins=dict(self.expected,policy_digest='a'*64)
  with self.assertRaises(ValueError):consume_report(self.raw,expected=pins)
 def test_duplicate_json_and_nonfinite_refuse(self):
  for raw in ['{"schema":1,"schema":2}',self.raw.replace('"actions":[1,4]','"actions":[NaN,4]'),self.raw.replace('"actions":[1,4]','"actions":[1e9999,4]')]:
   with self.assertRaises(ValueError):consume_report(raw,expected=self.expected)
 def test_size_depth_and_utf8_refuse(self):
  for raw in [b'\xff',' '*1048577,'['*2000+'0'+']'*2000]:
   with self.assertRaises(ValueError):consume_report(raw,expected=self.expected)
 def test_bad_rational_refuses(self):
  for n,d in [('1','0'),('01','2'),('NaN','1'),('9'*200,'1')]:
   r=json.loads(self.raw);key=next(k for k,v in r['hands'].items() if v['observed_combinations']);r['hands'][key]['explicit_hero_mass']={'rational':{'numerator':n,'denominator':d}}
   with self.assertRaises(ValueError):consume_report(json.dumps(r),expected=self.expected)
 def test_missing_duplicate_combo_or_class_refuses(self):
  r=copy.deepcopy(self.report);r['hands'].pop('AA')
  with self.assertRaises(ValueError):self.consume(r)
  r=copy.deepcopy(self.report);r['combo_provenance']*=2
  with self.assertRaises(ValueError):self.consume(r)
 def test_count_mass_and_mean_tamper_refuse(self):
  key=next(k for k,v in self.report['hands'].items() if v['observed_combinations'])
  for field,value in [('observed_combinations',2),('explicit_hero_mass',F(2)),('observed_action_values',[F(0),F(0)])]:
   r=copy.deepcopy(self.report);r['hands'][key][field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):self.consume(r)
 def test_unknown_ev_or_frequency_injection_refuses(self):
  for key,value in [('hand169_ev',F(2)),('native_infoset_ev',0),('frequencies',[F(1)])]:
   r=copy.deepcopy(self.report);r[key]=value
   with self.assertRaises(ValueError):self.consume(r)
 def test_render_and_cli_roundtrip(self):
  out=self.consume();html=render_html(out);self.assertIn('部分coverage',html);self.assertIn('アクション頻度：未提供',html);self.assertNotIn('<script',html)
  cmd=[sys.executable,'-B','-m','gto.native.action_report']
  for key,value in self.expected.items():cmd+=['--expected-'+key.removesuffix('_digest').replace('_','-'),value]
  p=subprocess.run(cmd,input=self.raw,text=True,capture_output=True);self.assertEqual(p.returncode,0);self.assertEqual(json.loads(p.stdout),out)
 def test_legacy_report_warns_not_validated(self):
  r=copy.deepcopy(self.report);r.pop('public_cards')
  for row in r['combo_provenance']:row.pop('action_values')
  out=self.consume(r);self.assertIn('LEGACY_PROVENANCE_NOT_RECOMPUTABLE',out['warnings']);self.assertEqual(out['validation'],'structure_and_pinned_identity_only')
 def test_bool_actions_and_coverage_flag_refuse(self):
  for change in ['actions','coverage']:
   r=copy.deepcopy(self.report)
   if change=='actions':r['actions']=[True,4]
   else:r['hands']['AA']['coverage_complete']=1
   with self.assertRaises(ValueError):self.consume(r)
 def test_nested_action_and_cli_rejection_are_bounded(self):
  r=copy.deepcopy(self.report);r['actions']=[{}]
  with self.assertRaises(ValueError):self.consume(r)
  cmd=[sys.executable,'-B','-m','gto.native.action_report']
  for key,value in self.expected.items():cmd+=['--expected-'+key.removesuffix('_digest'),value]
  p=subprocess.run(cmd,input=json.dumps({'actions':[{}]}),text=True,capture_output=True)
  self.assertEqual(p.returncode,2);self.assertEqual(p.stderr.strip(),'INVALID_ACTION_REPORT');self.assertEqual(p.stdout,'')
 def test_legacy_values_withheld(self):
  r=copy.deepcopy(self.report);r.pop('public_cards')
  for row in r['combo_provenance']:row.pop('action_values')
  out=self.consume(r);self.assertTrue(all(h['observed_action_values'] is None for h in out['hands']))
 def test_renderer_escapes_untrusted_display_strings(self):
  out=self.consume();out['policy_digest']='<img src=x onerror=alert(1)>'
  self.assertNotIn('<img',render_html(out));self.assertIn('&lt;img',render_html(out))
 def test_wrong_board_and_unsupported_schema_refuse(self):
  for key,value in [('public_cards',[0,1,2]),('schema','unknown')]:
   r=copy.deepcopy(self.report);r[key]=value
   with self.assertRaises(ValueError):self.consume(r)

if __name__=='__main__':unittest.main()
