"""Partial canonical preflop EVs using internal range continuation. NOT all-action QA."""
import argparse,copy,json,math,random,time
from pathlib import Path
from gto.qualification.range_continuation import load
from gto.qualification.mccfr_evaluate import open_posterior
from gto.qualification.native_mccfr import betting
from gto.qualification.policy import act,legal
from gto.qualification.public_response import observe
from gto.qualification.action_native import native_value
from gto.qualification.evaluate import atomic
from gto.abstract.model import classes,CLASSES
from gto.native.training import NativeGame
ARTIFACT='docs/qa/release-route-20261118/strategy.json.gz'
class Forced:
    def __init__(self,p,prefix):self.p,self.prefix=p,prefix
    def row(self,o,average=False):
        if len(o.history)<len(self.prefix):
            a=self.prefix[len(o.history)]
            if a not in o.actions:raise ValueError('illegal forced preflop prefix')
            return [float(x==a) for x in o.actions]
        return self.p.row(o,True)

def evaluate(build,library,out):
    p=load(build,ARTIFACT,library);reach,posterior,opens=open_posterior(p);rng=random.Random(17118207);reports=[];start=time.monotonic();game=NativeGame([100,100])
    for context,owner,prefix in [('rfi_open3',0,[8]),('vsopen_threebet10',1,[8,22])]:
        hands={};weights=[len(g)/1326 for g in classes()] if owner==0 else posterior
        for label,group in zip(CLASSES,classes()):
            if time.monotonic()-start>30:
                atomic(out,dict(status='INCOMPLETE_TIME_LIMIT',policy_digest=p.policy_digest,reports=reports,partial_context=context,partial_hands=hands,full_all169_action_precision='UNKNOWN'));return
            own=list(rng.choice(group));available=[c for c in range(52) if c not in own]
            for attempts in range(100000):
                other=rng.sample(available,7)
                if owner==0 or rng.random()<opens[tuple(sorted(other[:2]))]:break
            else:raise RuntimeError('conditional source rejection cap')
            deck=(own+other[:2] if owner==0 else other[:2]+own)+other[2:];tape=rng.getrandbits(128)
            value=native_value(Forced(p,prefix),p.native,game,deck,tape)*(1 if owner==0 else -1)
            hands[label]=dict(n=1,forced_prefix=prefix,action_EV_point_bb=value,sampling_interval_bb=None,precision_pass=False)
            if len(hands)%32==0:atomic(str(out)+'.progress.json',dict(context=context,completed=len(hands),policy_digest=p.policy_digest,rng=rng.getstate(),hands=hands))
        reports.append(dict(context=context,hands=hands,class_weights=weights,aggregate_action_EV_point_bb=sum(w*hands[l]['action_EV_point_bb'] for l,w in zip(CLASSES,weights)),
            aggregate_interval_bb=None,source_open_reach=reach if owner else None,scope='all169classes but ONLY one specified action/context,1sample/class; not baseline profileEV or all-action precision'))
    atomic(out,dict(status='PARTIAL_CANONICAL_ACTION_EV_UNVERIFIED',policy_digest=p.policy_digest,seed=17118207,native_paths=338,seconds=time.monotonic()-start,
        reports=reports,full_all169_action_precision='UNKNOWN',full_BR_upper_bb=None,nashconv_upper_bb=None,ordinary_registry_admission=False,verified_strategy_count=0))

def legal_scan(build,library,out):
    p=load(build,ARTIFACT,library);start=time.monotonic();checks=0;nativechecks=0
    private=[(48,49),(0,1),(40,44)];board=[4,9,14,19,24];game=NativeGame([100,100])
    def check(b,actions,public):
        nonlocal checks,nativechecks
        state=p.native.NativeState(game)
        for c in (48,49,0,1):state.apply_action(c)
        for a in actions:
            while state.is_chance_node():state.apply_action(board[len(state.audit()['board'])])
            state.apply_action(a)
        while state.is_chance_node():state.apply_action(board[len(state.audit()['board'])])
        if state.is_terminal():return
        assert legal(b)==state.legal_actions();nativechecks+=1
        for own in private:
            o=observe(b,own,public);row=p.row(o,True)
            assert len(row)==len(o.actions) and all(x>=0 and math.isfinite(x) for x in row) and abs(sum(row)-1)<1e-10
            checks+=1
    for prefix in ([],[8],[8,22]):
        root=betting(p.rules)
        for a in prefix:act(root,a)
        for a in legal(root):
            if a<=1:continue
            b=copy.deepcopy(root);act(b,a)
            if not b.done and b.round==0:check(b,prefix+[a],[])
    root=betting(p.rules);act(root,8);act(root,1);prefix=[8,1]
    for street in (1,2,3):
        for a in legal(root):
            if a<=1:continue
            if time.monotonic()-start>25:raise RuntimeError('size legality scan cap')
            b=copy.deepcopy(root);act(b,a)
            if not b.done:check(b,prefix+[a],board[:(0,3,4,5)[street]])
        if street<3:act(root,1);act(root,1);prefix.extend([1,1])
    atomic(out,dict(status='LEGALITY_ONLY_PASS_NOT_ACCURACY',seconds=time.monotonic()-start,native_public_states=nativechecks,private_rows=checks,policy_digest=p.policy_digest,
        omitted_size_error_bb=None,full_BR_upper_bb=None,ordinary_registry_admission=False,verified_strategy_count=0))

if __name__=='__main__':
    q=argparse.ArgumentParser();q.add_argument('--build',required=True);q.add_argument('--library',required=True);q.add_argument('--output',required=True);q.add_argument('--legal-scan',action='store_true');a=q.parse_args()
    (legal_scan if a.legal_scan else evaluate)(a.build,a.library,a.output)
