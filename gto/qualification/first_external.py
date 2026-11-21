"""Enumerate first traverser decision, then unbiased sampled continuation. Research."""
import copy,math,random
from pathlib import Path
from gto.qualification.action_baseline import ActionBaselineSolver,proposal,public_spot
from gto.qualification.native_mccfr import betting,choose
from gto.qualification.public_response import observe
from gto.qualification.policy import act,sha

class FirstExternalSolver(ActionBaselineSolver):
    def __init__(self,rules,native):
        super().__init__(rules,native,baseline=True,targeted=True)
        self.id={**self.id,'first_external_source_sha256':sha(Path(__file__)),
            'enumeration':'first traverser node only; all legal native actions'}
    def adopt(self,base,seed):
        # Explicit new experiment; source state remains untouched.
        for field in ('rows','iteration','visits','average_iterations','origin','source_average_digest','warm_corrected_sha'):
            setattr(self,field,copy.deepcopy(getattr(base,field)))
        self.rng.seed(seed)
        self.id={**self.id,'warm_source_digest':base.policy_digest}
    def collect(self,owner,deck,rng):
        holes=[deck[:2],deck[2:4]];regrets=[];averages=[]
        def walk(b,logreach,logq,enumerated,stream):
            if b.done:
                return b.settle([self.native.rank7(h+deck[4:]) for h in holes],b.round>=1)['net'][owner]/2
            if len(b.history)>512:raise RuntimeError('path budget')
            p=b.actor;o=self.observation(observe(b,holes[p],deck[4:4+(0,3,4,5)[b.round]]));pi=self.row(o)
            scale=math.exp(logreach[1-owner]-logq) if logreach[1-owner]!=-math.inf else 0.
            if p!=owner:
                weight=math.exp(logreach[p]-logq) if logreach[p]!=-math.inf else 0.
                averages.append((o,pi,weight))
            if p==owner and not enumerated:
                vals=[]
                for a,prob in zip(o.actions,pi):
                    child=copy.deepcopy(b);act(child,a);reach=logreach[:]
                    reach[p]=reach[p]+math.log(prob) if prob else -math.inf
                    vals.append(walk(child,reach,logq,True,random.Random(stream.getrandbits(128))))
            else:
                q=proposal(pi,o.actions,public_spot(o),p==owner,self.targeted)
                a=choose(o.actions,q,stream);j=o.actions.index(a);reach=logreach[:]
                reach[p]=reach[p]+math.log(pi[j]) if pi[j] else -math.inf
                baseline=self.baseline(o,owner);act(b,a)
                child=walk(b,reach,logq+math.log(q[j]),enumerated,stream)
                vals=baseline[:];vals[j]+=(child-baseline[j])/q[j]
            value=math.fsum(prob*v for prob,v in zip(pi,vals))
            if p==owner:regrets.append((o,pi,[(v-value)*scale for v in vals],0.))
            return value
        walk(betting(self.rules),[0.,0.],0.,False,rng)
        return regrets,averages
