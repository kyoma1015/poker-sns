import sys,os,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()));sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR'])
from gto.native.test_infoset_export import Export
from gto.native.infoset_export import export_action_classes,report_json
Export.setUpClass();test=Export();test.setUp();record=test.record()
report=export_action_classes([record]);raw=report_json(report)
print(json.dumps({'report':json.loads(raw),'sha256':hashlib.sha256(raw.encode()).hexdigest()},sort_keys=True))
