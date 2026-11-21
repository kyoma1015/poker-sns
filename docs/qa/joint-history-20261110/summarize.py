"""Publish only complete independently measured research points; preserve failures."""
import json,hashlib,gzip,base64,shutil
from pathlib import Path
from gto.abstract.joint_update_report import checked,improves
from gto.abstract.joint_stream_export import export

def run():
 root=Path(__file__).resolve().parent;old=json.loads((root.parent/'joint-updates-20261108/results.json').read_text());baseline=old['frozen_baseline'];points={};coverage={}
 files={'alternating4':Path('/workspace/joint-alternating-run/epoch4.json'),'alternating5':Path('/workspace/joint-alternating-run/epoch5.json'),'mixture025':Path('/workspace/joint-realization-run/result.json')}
 for name,path in files.items():
  raw=path.read_bytes();(root/(name+'.json')).write_bytes(raw);r=json.loads(raw)
  if r['coverage']!=1:
   points[name]={'status':'PARTIAL','coverage':r['coverage'],'nashconv_interval':r['restricted_nashconv_interval_bb']};continue
  metric=checked(r);metric.update(status='COMPLETE',epoch=r['epoch'],improves_frozen=improves(metric['nashconv_bb'],baseline['nashconv_bb']),delta_frozen_bb=metric['nashconv_bb']-baseline['nashconv_bb'],source_sha256=hashlib.sha256(raw).hexdigest());points[name]=metric
  ranges=export(r);payload=json.dumps(ranges,sort_keys=True,separators=(',',':')).encode();(root/(name+'-research-ranges.json.gz.b64')).write_bytes(base64.b64encode(gzip.compress(payload,mtime=0))+b'\n');coverage[name]={'contexts':4,'hand_rows':sum(len(x['hands']) for x in ranges['ranges']),'action_ev_cells':sum(len(h['action_ev_bb']) for x in ranges['ranges'] for h in x['hands']),'normal':False,'UI_added':0}
 best={'name':'immutable_frozen','nashconv_bb':baseline['nashconv_bb']}
 for name,metric in points.items():
  if metric['status']=='COMPLETE' and improves(metric['nashconv_bb'],best['nashconv_bb']):best={'name':name,'nashconv_bb':metric['nashconv_bb']}
 vector=json.loads(Path('/workspace/joint-vector-population/result.json').read_text());ratio=vector['backend_cpu']['original']/vector['backend_cpu']['vector'];result={'baseline':baseline,'parent_cfrplus3':old['methods']['cfr_plus'][-1],'points':points,'selected_same_game_profile':best,'vector_full_population_pass':vector['full_population_pass'],'vector_call_cpu_speedup':ratio,'formal_acceptance':[0,12],'normal_GTO_added':0,'UI_added':0,'coverage':coverage,'real_game_error':'UNKNOWN','external_GTO':'NOT PERFORMED','selection_scope':'same limited optimization game,not holdout/fullNLHE accuracy'};(root/'results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 for src,dest in [('/workspace/joint-vector-population/result.json','vector-population-result.json'),('/workspace/joint-alternating-runtime.json','runtime-kernel-pin.json'),('/workspace/joint-history-current-diagnostic.json','rejected-current-policy-diagnostic.json'),('/workspace/joint-history-measurement-completion/raw-receipt.json','raw-completion-receipt.json'),('/workspace/joint-updates-recovery-receipt.json','initial-recovery-receipt.json'),('/workspace/joint-recovery-CI-proof-9bf6.json','recovery-CI-proof.json')]:shutil.copyfile(src,root/dest)
 cuts=root/'original-budget-partials';cuts.mkdir(exist_ok=True)
 for p in Path('/workspace/joint-history-measurement-completion').glob('*-original-partial.json'):shutil.copyfile(p,cuts/p.name)
 print(json.dumps({'selected':best,'points':{k:v.get('nashconv_bb') for k,v in points.items()},'vector_speedup':ratio,'coverage':coverage}))
if __name__=='__main__':run()
