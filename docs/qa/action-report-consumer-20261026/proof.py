import os,sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()));sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR'])
from gto.native.test_infoset_export import Export
from gto.native.infoset_export import export_action_classes,report_json
from gto.native.action_report import consume_report,render_html
Export.setUpClass();fixture=Export();fixture.setUp();report=export_action_classes([fixture.record()]);raw=report_json(report)
view=consume_report(raw,expected={k:report[k] for k in ['policy_digest','config_digest','observation_digest']})
print(json.dumps({'producer':json.loads(raw),'consumer':view,'view_sha256':hashlib.sha256(json.dumps(view,sort_keys=True).encode()).hexdigest(),'html_sha256':hashlib.sha256(render_html(view).encode()).hexdigest()},sort_keys=True))
