"""Actual owner-row recovery and completion-free evaluation, never GTO data."""
import hashlib,json
from pathlib import Path
from gto.native.training import NativeGame,checkpoint
from gto.native.checkpoints import load_verified_checkpoint
from gto.native.infoset_export import _digest
from gto.native.preflop import decision
from gto.native.ordinary_study import context_coverage
from gto.native.hu_preflop_reach import reached_classes
from gto.native.strict_continuation import CheckpointPolicy,evaluate,diagnose

TARGETS=((20,6),(26,10),(39,15),(43,8))

def target_keys(native,game):
    keys=[]
    for pair in TARGETS:
        other=[c for c in range(52) if c not in pair][:2]
        node=decision(native,game,[7,20,44],cards=other+list(pair))
        if node.current_player()!=1:raise ValueError('expected BB vs4bet')
        keys.append(node.information_state_string(1))
    return keys

def owner_rows(solver,keys):
    result=[]
    for pair,key in zip(TARGETS,keys):
        try:row=solver.row(key)
        except IndexError:row={'updates':0,'visits':0}
        result.append({'hand':list(pair),'updates':row['updates'],'visits':row['visits']})
    return result

def experiment(native,runtime,parent_directory,output,*,reference=None):
    runtime=Path(runtime);parent_directory=Path(parent_directory);output=Path(output);output.mkdir(exist_ok=False)
    parent=parent_directory/'seed-29-100000.bin';parent_meta=json.loads((parent_directory/'seed-29-100000.json').read_text())
    parent_sha=hashlib.sha256(parent.read_bytes()).hexdigest()
    if parent_sha!=parent_meta['source_checkpoint_sha256']:raise ValueError('parent observation/checkpoint differs')
    manifest=json.loads((runtime/'focused/manifest.json').read_text())
    original=json.loads((runtime/'targeted/manifest.json').read_text());game=NativeGame([100,100])
    old_contract=original['contract']+':'+_digest(json.loads(game._public_config_json))
    solver=native.Solver(game,.6,29,True,True,.1)
    # Explicit migration only: read-only original checksum/contract, identical
    # fields/modes/RNG. New outputs use source+parent-specific contracts.
    imported=load_verified_checkpoint(solver,parent,old_contract)
    if solver.iteration!=100000 or imported['iteration']!=100000:raise ValueError('wrong source iteration')
    keys=target_keys(native,game);before=owner_rows(solver,keys)
    if any(row['updates'] for row in before):raise ValueError('expected four genuine unlearned owner rows')
    rounds=[]
    for _ in range(8):
        for _ in range(64):solver.run_iteration()
        rows=owner_rows(solver,keys);rounds.append({'iteration':solver.iteration,'rows':rows})
        if all(row['updates']>0 for row in rows):break
    if not all(row['updates']>0 for row in rows):raise ValueError('bounded owner-row recovery incomplete')
    contract=manifest['contract']+':parent:'+parent_sha+':game:'+_digest(json.loads(game._public_config_json))
    path=output/'focused.bin';checkpoint(solver,path,contract);sha=hashlib.sha256(path.read_bytes()).hexdigest()
    rng=solver.rng_state();restored=native.Solver(game,.6,29,True,True,.1);load_verified_checkpoint(restored,path,contract)
    if restored.rng_state()!=rng or restored.iteration!=solver.iteration or owner_rows(restored,keys)!=rows:
        raise ValueError('focused checkpoint/RNG restoration differs')
    del solver;solver=restored
    contexts=[]
    for history in ([],[7],[7,20],[7,20,44]):
        context=context_coverage(native,solver,game,history)
        if history:context['history_reach']=reached_classes(native,solver,game,history)
        coverage=context['history_reach']['complete_frequency_classes'] if history else context['complete_frequency_classes']
        if coverage!=169 or context['updated_orderings']!=2652:raise ValueError('actual learned/reach class coverage incomplete')
        contexts.append(context)
    audit=diagnose(native,solver,game)
    policy=CheckpointPolicy(native,solver,sha)
    strict=evaluate(native,game,policy);replay=evaluate(native,game,policy)
    if strict!=replay:raise ValueError('strict learned-only evaluation replay differs')
    report={'schema':'pokerid-focused-owner-recovery-v1','formal_profile':False,'parent_sha256':parent_sha,
      'parent_source_contract':old_contract,'new_source_contract':contract,'source_manifest':manifest,
      'iteration':solver.iteration,'additional_iterations':solver.iteration-100000,'before':before,'progress':rounds,
      'checkpoint_sha256':sha,'checkpoint_and_rng_restored':True,'frequency_and_ev_same_checkpoint':True,
      'contexts':contexts,'infoset_diagnosis':audit,'strict_evaluation':strict,'strict_same_samples_replayed':True,
      'independent_statistical_sample_sets':1,'ordinary_verified_gto_ranges':0,'formal_acceptance_complete':0,
      'full_game_convergence_verified':False}
    if reference is not None:
        from gto.native.replay_reference import verify
        report['cross_build_replay']=verify(report,json.loads(Path(reference).read_text()))
    (output/'evidence.json').write_text(json.dumps(report,sort_keys=True)+'\n')
    summary={k:v for k,v in report.items() if k not in ('contexts','strict_evaluation')}
    summary['contexts']=[{'stage':c['stage'],'updated_orderings':c['updated_orderings'],
        'complete_frequency_classes':c.get('history_reach',{}).get('complete_frequency_classes',c['complete_frequency_classes'])} for c in contexts]
    summary['strict_evaluation']=strict
    print('FOCUSED_EVIDENCE '+json.dumps(summary,sort_keys=True),flush=True)
    return report
if __name__=='__main__':
 import argparse,importlib,sys
 p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);p.add_argument('--parent-directory',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reference',type=Path)
 a=p.parse_args();sys.path.insert(0,str(a.runtime/'focused'))
 experiment(importlib.import_module('pokerid_focused'),a.runtime,a.parent_directory,a.output,reference=a.reference)
