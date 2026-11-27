"""Same causal native row function, with vectorized chance-weighted parent cache."""
from collections import Counter
from pathlib import Path
import hashlib
import numpy as np
from gto.qualification.active_policy import Policy as Original
from gto.qualification import active_policy
from gto.qualification.native_mccfr import digest
from gto.qualification.policy import sha

class Policy(Original):
    def __init__(self,q,fallback,identity):
        self.q=q;self.fallback=fallback;self.native=fallback.native;self.rules=fallback.rules
        self.pi=q.policy();self.stats={r:Counter() for r in range(4)};self.cache={}
        self.known={(n['round'],tuple(tuple(h) for h in n['native_prefix'])):k for k,n in enumerate(q.nodes) if n['actor']>=0}
        self.ancestors=[[] for _ in q.nodes]
        for k,n in enumerate(q.nodes):
            for c in n['children']:self.ancestors[c]=self.ancestors[k]+([k] if n['actor']>=0 else [])
        self.lookup=[];self.backoff=[]
        for k,n in enumerate(q.nodes):
            if n['actor']<0:self.lookup.append({});self.backoff.append({});continue
            count=len(n['children']);keys=q.keys[k];t=len(keys);st=q.base[k]
            self.lookup.append({key:st+j*count for j,key in enumerate(keys)})
            mass=np.zeros(t)
            for b,block in enumerate(q.blocks):mass+=np.bincount((q.active[b,k]-st)//count,minlength=t)*block['weight']/1081
            code=np.array([key[0] for key in keys]);unique,inv=np.unique(code,return_inverse=True);den=np.bincount(inv,weights=mass);pi=self.pi[st:st+t*count].reshape(t,count)
            sums=np.stack([np.bincount(inv,weights=mass*pi[:,j],minlength=len(unique)) for j in range(count)],axis=1)
            self.backoff.append({int(c):row/d for c,row,d in zip(unique,sums,den) if d>0})
        self._digest=digest(dict(identity=identity,fallback=fallback.policy_digest,pi_sha256=hashlib.sha256(self.pi.astype('<f8').tobytes()).hexdigest(),adapter_sha256=sha(Path(__file__)),row_source_sha256=sha(Path(active_policy.__file__))))
