"""Native embedding of the full-public sampling optimizer's declared defaults.
Known public nodes with unseen coarse cells use explicit uniform research prior;
unknown public histories still use protected legal Sparse, never blanket fold.
"""
from pathlib import Path
from gto.qualification import stream_policy
from gto.qualification.native_mccfr import digest
from gto.qualification.policy import sha

class Router:
    def __init__(self,fallback,q):
        self.base=fallback;self.native=fallback.native;self.rules=fallback.rules
        self.known={(n['round'],tuple(map(tuple,n['native_prefix']))):n['native_actions'] for n in q.nodes if n['actor']>=0}
        self.policy_digest=digest(dict(base=fallback.policy_digest,router_sha256=sha(Path(__file__)),known_actions=self.known_repr(q)))
    def known_repr(self,q):return [(n['round'],n.get('native_prefix'),n.get('native_actions')) for n in q.nodes if n['actor']>=0]
    def row(self,o,average=False):
        actions=self.known.get((o.round,tuple(tuple(h[:3]) for h in o.history)))
        if actions is None:return self.base.row(o,average)
        if any(a not in o.actions for a in actions):raise ValueError('native prior legality')
        return [float(a in actions)/len(actions) for a in o.actions]

class Policy(stream_policy.Policy):
    def __init__(self,q,fallback,identity):super().__init__(q,Router(fallback,q),identity)
