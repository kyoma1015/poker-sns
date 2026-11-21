"""Independent conditional native EVs for selected reduced-tree actions only."""
import argparse,gzip,json,random,time
from pathlib import Path
from gto.abstract import model
from gto.qualification.range_continuation import RangePolicy,HOLES,INDEX
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.preflop_reopt import ARTIFACT
from gto.qualification.range_continuation import load
from gto.qualification.range_preflop_ev import Forced
from gto.qualification.native_mccfr import betting
from gto.qualification.policy import act
from gto.qualification.public_response import observe
from gto.qualification.action_native import native_value,interval
from gto.qualification.evaluate import atomic
from gto.qualification.variance_study import compressed
from gto.native.training import NativeGame


def evaluate(build,library,out,resume=False):
    out=Path(out);prior=load(build,ARTIFACT,library);p=RangePolicy(load_policy(build,out/'range_reoptimized.json.gz'),prior.lib)
    contexts=[('rfi',0,[],[0,1,8]),('vs_open',1,[8],[0,1,22]),('vs_3bet',0,[8,22],[0,1,102])]
    saved=json.loads(gzip.decompress((out/'selected-action-EV.json.gz').read_bytes())) if resume else None
    if saved and saved['policy_digest']!=p.policy_digest:raise ValueError('resume policy mismatch')
    previous=saved['rows'] if saved else []
    rng=random.Random(17118303);rows=[];start=time.monotonic();worlds=[];game=NativeGame([100,100]);delta=.001/(169*9)
    for name,owner,prefix,actions in contexts:
        b=betting(p.rules)
        for a in prefix:act(b,a)
        # Opponent's public action likelihood, computed with own-only observation.
        opponent=betting(p.rules)
        if owner==0 and prefix:act(opponent,8)
        target=8 if owner==1 else 22
        likelihood=[1.]*1326 if not prefix else [p.base.row(observe(opponent,h,[]),True)[observe(opponent,h,[]).actions.index(target)] for h in HOLES]
        for label,group in zip(model.CLASSES,model.classes()):
            if time.monotonic()-start>90:
                compressed(out/'selected-action-EV.json.gz',dict(status='INCOMPLETE_TIME_LIMIT',policy_digest=p.policy_digest,rows=rows,worlds=worlds));return
            samples=[[] for _ in actions]
            for _ in range(2):
                own=list(rng.choice(group));compatible=[h for h in HOLES if not set(h).intersection(own)]
                weights=[likelihood[INDEX[h]] for h in compatible]
                if sum(weights)<=0:raise ValueError('zero conditional private range')
                other=list(rng.choices(compatible,weights=weights,k=1)[0]);board=rng.sample([c for c in range(52) if c not in own+other],5);tape=rng.getrandbits(128)
                deck=(own+other if owner==0 else other+own)+board;worlds.append(dict(context=name,hand=label,deck=deck,tape=tape))
                if len(rows)<len(previous):continue
                for a,vs in zip(actions,samples):vs.append(native_value(Forced(p,prefix+[a]),p.native,game,deck,tape)*(1 if owner==0 else -1))
            if len(rows)<len(previous):
                old=previous[len(rows)]
                if (old['context'],old['hand'],old['actions'])!=(name,label,actions):raise ValueError('resume row mismatch')
                rows.append(old);continue
            rows.append(dict(context=name,hand=label,actions=actions,action_EV_bb=[interval(v,-50,50,delta) for v in samples]))
            if len(rows)%32==0:
                compressed(out/'selected-action-EV.json.gz',dict(status='INCOMPLETE_CHECKPOINT',policy_digest=p.policy_digest,rows=rows,worlds=worlds))
                print(json.dumps(dict(conditional_hand_rows=len(rows),seconds=time.monotonic()-start)),flush=True)
    maxwidth=max(x['interval'][1]-x['interval'][0] for r in rows for x in r['action_EV_bb'])
    compressed(out/'selected-action-EV.json.gz',dict(status='COMPLETE_SELECTED_ACTIONS_UNVERIFIED',policy_digest=p.policy_digest,rows=rows,worlds=worlds,seed=17118303,native_paths=len(rows)*6,
        confidence_family=.999,max_interval_width_bb=maxwidth,full_legal_action_EV_precision_bb=None,omitted_size_error_bb=None,precision_pass=False,seconds=time.monotonic()-start,
        note='2 samples/hand/context/action; conditional action EV, not root-weighted EV; interval bounds are not convergence evidence'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--library',required=True);p.add_argument('--out',required=True);p.add_argument('--resume',action='store_true');a=p.parse_args();evaluate(a.build,a.library,a.out,a.resume)
