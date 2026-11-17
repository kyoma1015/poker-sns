"""Full-support realization-average updates using the other player's traversal.

The traverser explores all legal actions. On its path the NON-traverser's own
realization-positive histories have sampling support, even when traverser's
current target assigns probability zero to a public action. Warm R/RNG reused;
legacy S archived in the immutable source, not mixed into corrected sums.
"""
from collections import Counter
import math
import random
from pathlib import Path
from gto.qualification.native_mccfr import betting,choose,digest
from gto.qualification.policy import act,sha
from gto.qualification.public_response import observe
from gto.qualification.variance_mccfr import VarianceSolver,cv_updates


class AverageSupportSolver(VarianceSolver):
    def __init__(self,rules,native,seed=1201117,*,correct=True):
        super().__init__(rules,native,seed,suits=True,control=False)
        self.correct=correct;self.average_counts=Counter();self.average_iterations=0
        self.source_average_digest=None
        self.id={**self.id,'average_support_sha256':sha(Path(__file__)),
                 'average_actor':'nontraverser' if correct else 'traverser-control',
                 'updates':'simultaneous-pair-same-deal-independent-action-streams',
                 'warm_average':'new accumulator; legacy S preserved at origin'}

    def migrate(self,data):
        super().migrate(data)
        self.source_average_digest=digest({k:v['S'] for k,v in data['rows'].items()})
        for row in self.rows.values():row['S']=[0.]*len(row['S'])

    def snapshot(self):
        return {**super().snapshot(),'average_counts':dict(self.average_counts),
                'average_iterations':self.average_iterations,'source_average_digest':self.source_average_digest}

    def restore(self,data):
        super().restore(data);self.average_counts=Counter(data['average_counts'])
        self.average_iterations=data['average_iterations'];self.source_average_digest=data['source_average_digest']

    def collect(self,owner,deck,rng):
        b=betting(self.rules);holes=[deck[:2],deck[2:4]];reach=[1.,1.]
        records=[];averages=[];logq=0.;ownq=0.
        while not b.done:
            o=self.observation(observe(b,holes[b.actor],deck[4:4+(0,3,4,5)[b.round]]))
            pi=self.row(o);p=b.actor
            if (p!=owner)==self.correct:
                averages.append((o,pi,reach[p]*math.exp(-logq)))
            q=[.6/len(pi)+.4*w for w in pi] if p==owner else pi
            a=choose(o.actions,q,rng);index=o.actions.index(a)
            if p==owner:
                records.append((o,pi,index,q[index],ownq,0.,[0.]*len(pi)))
                ownq+=math.log(q[index])
            reach[p]*=pi[index];logq+=math.log(q[index]);act(b,a)
            if len(b.history)>512:raise RuntimeError('path budget')
        ranks=[self.native.rank7(h+deck[4:]) for h in holes]
        utility=b.settle(ranks,b.round>=1)['net'][owner]/2
        return list(cv_updates(records,utility)),averages

    def step(self):
        deck=self.rng.sample(range(52),9)
        # Freeze both regret strategies until both samples are complete. The
        # master stream only deals/reserves seeds; sampled paths cannot rewind it.
        batches=[self.collect(p,deck,random.Random(self.rng.getrandbits(128))) for p in (0,1)]
        for regrets,averages in batches:
            for o,pi,delta,_ in regrets:
                row=self.rows.setdefault(o.key,dict(actions=list(o.actions),R=[0.]*len(pi),S=[0.]*len(pi)))
                row['R']=[x+y for x,y in zip(row['R'],delta)]
                if not all(math.isfinite(x) for x in row['R']):raise ArithmeticError('regret overflow')
                self.counts[o.key]+=1;self.visits+=1
            for o,pi,weight in averages:
                row=self.rows.setdefault(o.key,dict(actions=list(o.actions),R=[0.]*len(pi),S=[0.]*len(pi)))
                row['S']=[x+weight*p for x,p in zip(row['S'],pi)]
                if not all(math.isfinite(x) for x in row['S']):raise ArithmeticError('average overflow')
                self.average_counts[o.key]+=1
        self.iteration+=1;self.average_iterations+=1
