"""Predictable full-action baselines and full-support public-history proposals."""
import copy,gzip,json,math
from collections import Counter
from pathlib import Path
from gto.qualification.average_support import AverageSupportSolver
from gto.qualification.native_mccfr import betting,choose,digest,matching
from gto.qualification.policy import ROOT,act,hand,sha
from gto.qualification.public_response import observe
from gto.hand169 import CLASSES

BASELINE=ROOT/'docs/qa/mccfr-variance-20261117/average-corrected-evaluation.json.gz'


def public_spot(o):
    if o.round!=0:return None
    if not o.history and o.actor==0:return 'rfi'
    if len(o.history)==1 and o.history[0][0:3]==(0,0,6) and o.actor==1:return 'vs_3bb_open'
    if len(o.history)==2 and o.history[0][0:3]==(0,0,6) and o.history[1][0:3]==(0,1,20) and o.actor==0:return 'vs_10bb_3bet'
    return None


def proposal(pi,actions,spot,owner_node,targeted):
    if not owner_node and not targeted:return pi
    focus=8 if spot=='rfi' else 22 if spot=='vs_3bb_open' else None
    return [.4*p+.6*((.5/len(pi)+.5*(a==focus)) if targeted and focus in actions else 1/len(pi)) for a,p in zip(actions,pi)]


def general_updates(records,utility):
    """All-actor recursive control variate, full counterfactual pi/q correction."""
    value=utility
    for o,pi,index,q,scale,baseline,is_owner in reversed(records):
        values=list(baseline);values[index]+=(value-baseline[index])/q
        value=math.fsum(p*v for p,v in zip(pi,values))
        if is_owner:yield o,pi,[(v-value)*scale for v in values],0.


class ActionBaselineSolver(AverageSupportSolver):
    def __init__(self,rules,native,*,baseline=False,targeted=False,current=False):
        super().__init__(rules,native,correct=True)
        self.use_baseline,self.targeted,self.current_behavior=baseline,targeted,current
        self.predictions={r['context']:r['hands'] for r in json.loads(gzip.decompress(BASELINE.read_bytes()))['reports']}
        self.id={**self.id,'action_baseline_sha256':sha(Path(__file__)),
                 'prediction_sha256':sha(BASELINE),'use_predictions':baseline,'targeted':targeted,
                 'behavior':'current' if current else 'average',
                 'proposal':'0.4target+0.6proposal; proposal half-uniform half-focus when legal'}
        self.warm_corrected_sha=None;self.diagnostic_sums={};self.reach_counts=Counter()

    def row(self,o,average=False):
        return super().row(o,average and not self.current_behavior)

    @property
    def policy_digest(self):
        field='R' if self.current_behavior else 'S'
        return digest(dict(identity=self.id,rows={k:matching(v[field]) for k,v in self.rows.items()}))

    def current_view(self):
        view=copy.copy(self);view.current_behavior=True;view.id={**self.id,'behavior':'current'}
        return view

    def warm(self,data):
        original=AverageSupportSolver(self.rules,self.native);original.restore(data)
        self.rows=copy.deepcopy(original.rows);self.rng.setstate(original.rng.getstate())
        self.iteration=original.iteration;self.visits=original.visits
        self.average_iterations=original.average_iterations;self.origin=original.origin
        self.source_average_digest=original.source_average_digest;self.warm_corrected_sha=digest(data)
        self.counts=Counter();self.average_counts=Counter()

    def snapshot(self):
        return {**super().snapshot(),'warm_corrected_sha':self.warm_corrected_sha,'reach_counts':dict(self.reach_counts)}

    def restore(self,data):
        super().restore(data);self.warm_corrected_sha=data['warm_corrected_sha'];self.reach_counts=Counter(data['reach_counts'])

    def baseline(self,o,owner):
        if not self.use_baseline:return [0.]*len(o.actions)
        table=self.predictions.get(public_spot(o),{}).get(CLASSES[hand(o.own)],{}).get('action_ev_bb',{})
        sign=1 if o.actor==owner else -1
        return [sign*(-(o.live[o.actor]+o.dead[o.actor])/2 if a==0 else table.get(str(a),{}).get('mean',0.)) for a in o.actions]

    def collect(self,owner,deck,rng):
        b=betting(self.rules);holes=[deck[:2],deck[2:4]];logreach=[0.,0.]
        records=[];averages=[];logq=0.
        while not b.done:
            o=self.observation(observe(b,holes[b.actor],deck[4:4+(0,3,4,5)[b.round]]))
            pi=self.row(o);p=b.actor;spot=public_spot(o)
            if p!=owner:
                w=math.exp(logreach[p]-logq) if logreach[p]!=-math.inf else 0.
                averages.append((o,pi,w))
                if w>0 and spot:self.reach_counts[spot]+=1
            q=proposal(pi,o.actions,spot,p==owner,self.targeted)
            a=choose(o.actions,q,rng);index=o.actions.index(a)
            scale=math.exp(logreach[1-owner]-logq) if logreach[1-owner]!=-math.inf else 0.
            records.append((o,pi,index,q[index],scale,self.baseline(o,owner),p==owner))
            logreach[p]=logreach[p]+math.log(pi[index]) if pi[index]>0 else -math.inf
            logq+=math.log(q[index]);act(b,a)
            if len(b.history)>512:raise RuntimeError('path budget')
        utility=b.settle([self.native.rank7(h+deck[4:]) for h in holes],b.round>=1)['net'][owner]/2
        return list(general_updates(records,utility)),averages
