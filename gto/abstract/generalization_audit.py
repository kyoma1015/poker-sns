"""Read-only post-lock evaluation on TRAIN/VALIDATION; never fits or selects.

This produces a comparable transfer-policy train/validation/test generalization
report, rather than comparing teacher training loss to a different student.
"""
import argparse,json,hashlib
from pathlib import Path
from gto.abstract import generalization_study as study
from gto.abstract import continuation_game as base
from gto.abstract.generalization_features import TransferPolicy,uniform_strength
from gto.abstract.generalization_game import game
from gto.abstract import flop_exact as exact

def audit(root,selection,path):
 if selection['protocol_sha256']!=study.sha(study.PROTOCOL) or selection['source_sha256']!=study.identities():raise ValueError('selection changed')
 protocol=json.loads(study.PROTOCOL.read_text());rank,lib,pi,digest=study.initialize(root);rows=[];models=selection['models'];config=selection['selected_config'];policies={k:TransferPolicy(v['records'],config,study.load(v['coarse'])) for k,v in models.items()}
 for split in ('train','validation'):
  for item in protocol['split'][split]:
   m=exact.matrix(rank,item['cards']);strength=uniform_strength(m)
   for stage in ('vs_3bet','vs_4bet'):
    g=game(lib,m,pi,stage,strength)
    for seed in protocol['learning_initialization_seeds']:
     model=models[study.model_key(stage,seed)];candidate=policies[study.model_key(stage,seed)].materialize(g);coarse=TransferPolicy([],{'kind':'coarse'},study.load(model['coarse'])).materialize(g)
     for name,p in (('selected',candidate),('retrained_coarse',coarse)):rows.append({'split':split,'method':name,'flop':item['cards'],'stage':stage,'seed':seed,'metrics':base.evaluate(g,p)})
 summaries={split:{name:study.values([r for r in rows if r['split']==split and r['method']==name]) for name in ('selected','retrained_coarse')} for split in ('train','validation')}
 return {'schema':'pokerid-post-lock-training-audit-v1','selection_sha256':study.sha(path),'policy_updated':False,'selection_performed':False,'final_boards_accessed':False,'rows':rows,'summaries':summaries,'sampling_error_bb':0,'numerical_guard_bb':1e-7,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'formal_acceptance_complete':0}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--selection',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=audit(a.build_dir,json.loads(a.selection.read_text()),a.selection);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps(r['summaries']))
