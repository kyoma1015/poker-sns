"""Bounded warm-R comparison of average estimators, no production strategy."""
import gzip,json,time
from pathlib import Path
from gto.qualification.average_support import AverageSupportSolver
from gto.qualification.build import load
from gto.qualification.variance_study import compressed
from gto.qualification.variance_evaluate import evaluate_solver
from gto.qualification.evaluate import atomic


def run(build,source,output):
    rules,native=load(build);data=json.loads(Path(source).read_text());out=Path(output);out.mkdir(parents=True,exist_ok=True)
    reports=[];nonzero=[]
    for correct in (False,True):
        name='average-corrected' if correct else 'average-control'
        s=AverageSupportSolver(rules,native,correct=correct);s.migrate(data)
        start=time.monotonic();i=0
        while i<128 and time.monotonic()-start<2:
            s.step();i+=1
            if i%32==0:compressed(out/(name+'-checkpoint.json.gz'),s.snapshot())
        elapsed=time.monotonic()-start;compressed(out/(name+'-checkpoint.json.gz'),s.snapshot())
        r=dict(name=name,policy_digest=s.policy_digest,paired_iterations=i,training_seconds=elapsed,
            total_infosets=len(s.rows),regret_updates=sum(s.counts.values()),regret_infosets=len(s.counts),
            average_updates=sum(s.average_counts.values()),average_infosets=len(s.average_counts),
            average_revisit_rate=1-len(s.average_counts)/sum(s.average_counts.values()),
            old_S_preserved_at_source=True,new_S_initialization='zero; only R/RNG reused')
        reports.append(r);nonzero.append({k:v['R'] for k,v in s.rows.items() if any(v['R'])})
        atomic(out/'average-comparison.json',dict(arms=reports,status='RUNNING'))
        evaluate_solver(s,out/(name+'-evaluation.json'))
    atomic(out/'average-comparison.json',dict(arms=reports,regrets_identical=nonzero[0]==nonzero[1],
        expanded_learning=False,status='BLOCKED_UNVERIFIED',formal_acceptance_complete=0))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args();run(a.build,a.source,a.output)
