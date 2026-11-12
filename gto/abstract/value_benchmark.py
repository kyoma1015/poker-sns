"""Readonly validation timing, not a model-selection or final-test phase."""
import argparse,json,math,time
from pathlib import Path
from gto.abstract import value_study as study,value_response as learning
from gto.abstract import flop_exact as exact,continuation_game as base,range_features as feature
from gto.abstract.factorial_game import game
from gto.abstract.generalization_features import uniform_strength


def run(root,limit=None):
 protocol=json.loads(study.PROTOCOL.read_text());path=study.ROOT/'selection.json';selection=json.loads(path.read_text());study.validate(selection,path);start=time.perf_counter();rank,lib,flib,pi,_=study.initialize(root);rlib=learning.build(root/'response');build_seconds=time.perf_counter()-start;rows=[];seed=protocol['learning_initialization_seeds'][0];config=selection['selected_config'];control=next(c for c in protocol['candidates'] if c['family']=='probability')
 for row in protocol['split']['validation'][:limit]:
  start=time.perf_counter();m=exact.matrix(rank,row['cards']);matrix_seconds=time.perf_counter()-start;uniform=uniform_strength(m)
  for stage in study.STAGES:
   start=time.perf_counter();g=game(lib,m,pi,stage,feature.books(flib,m,pi,stage,uniform));construction_seconds=time.perf_counter()-start;records=selection['models'][study.mk(stage,seed)]['records'];learner=learning.TargetTransfer(records,control);start=time.perf_counter();prior=learner.materialize(g);prediction_seconds=time.perf_counter()-start;start=time.perf_counter();baseline=base.evaluate(g,prior);baseline_metric_seconds=time.perf_counter()-start;start=time.perf_counter()
   if config['family']=='response':_,metric=learning.respond(rlib,g,prior,config['iterations'])
   else:metric=base.evaluate(g,learning.TargetTransfer(records,config).materialize(g))
   planning_seconds=time.perf_counter()-start
   for cfg,actual in ((control,baseline),(config,metric)):
    entry=next(c for c in selection['candidate_validation'] if c['config']['name']==cfg['name']);expected=next(x['metrics'] for x in entry['validation'] if x['flop']==row['cards'] and x['stage']==stage and x['seed']==seed)
    for k,v in expected.items():
     if isinstance(v,(int,float)) and not isinstance(v,bool) and not math.isclose(v,actual[k],rel_tol=1e-12,abs_tol=1e-12):raise ValueError('readonly benchmark differs from frozen validation')
   rows.append({'flop':row['cards'],'category':row['category'],'stage':stage,'seed':seed,'full_hole_runout_matrix_seconds_shared_between_stages':matrix_seconds,'features_and_game_seconds':construction_seconds,'cold_neighbor_probability_prediction_seconds':prediction_seconds,'control_exact_certification_seconds':baseline_metric_seconds,'selected_planning_and_exact_certification_seconds':planning_seconds,'control_nashconv_bb':baseline['restricted_nashconv_bb'],'selected_nashconv_bb':metric['restricted_nashconv_bb']})
 return {'rows':rows,'build_seconds':build_seconds,'selection_sha256':study.sha(path),'source_sha256':study.sha(__file__),'candidate_updated':False,'accessed_splits':['validation'],'scope':'single observed wall-time run; seed31; geometry cold per context; construction shared; not smartphone or cross-machine benchmark; exact metric certification included in planning time','external_gto_comparison':'NOT PERFORMED','real_game_approximation_error':'UNKNOWN'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--limit',type=int);a=p.parse_args();out=run(a.build_dir,a.limit);a.output.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({'contexts':len(out['rows']),'candidate_updated':False,'scope':out['scope']}))
