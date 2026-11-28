"""N-owner CFR+ in an explicit finite native all-in/fold/call research game.

Utilities remain N-dimensional, including rake. Restricted unilateral gains are
NOT fullnative NashConv, and multiplayer CFR has no HU minimax guarantee.
"""
import argparse,copy,itertools,json,math,random,time
from pathlib import Path
import numpy as np
from gto.qualification.public_response import Observation,MissingResponse
from gto.qualification.multiplayer_scope import checked_config,OfflineProfile
from gto.qualification.native_mccfr import digest
from gto.qualification.policy import sha
from gto.qualification.evaluate import atomic

def observation(s):
    a=s.audit();p=s.current_player()
    return Observation(p,tuple(sorted(a['holes'][p])),tuple(a['board']),a['round'],a['price'],a['last_full'],tuple(a['remaining']),tuple(a['street']),tuple(a['live']),tuple(a['dead']),tuple(a['folded']),tuple(tuple(h) for h in a['history']),tuple(s.legal_actions()))

def scoped_actions(o,scope):
    """Shared finite action law; legalofftree states never become implicitfold."""
    legal=o.actions
    if scope=='allin':return tuple(a for a in legal if a==0 or a==max(legal))
    if scope!='preflop':raise ValueError('explicit multiplayer action scope')
    if o.round>0:
        if 1 not in legal:raise ValueError('explicit native check/call unavailable')
        return (1,)
    raises=sum(h[0]==0 and h[2] not in (0,1) for h in o.history)
    targets=[a for a in legal if a not in (0,1)]
    wanted=(6,20)[raises]+2 if raises<2 else (max(targets) if targets else None)
    selected=wanted if wanted in targets else (max(targets) if targets else None)
    return tuple(a for a in legal if a in (0,1) or a==selected)

def clone_native(native,game,deck,state):
    """Thinbinding-compatible clone; replaysactualpublichistory, no fakeboards."""
    from gto.qualification.range_continuation import history_action
    n=game.num_players();result=native.NativeState(game)
    for c in deck[:2*n]:result.apply_action(c)
    for entry in state.audit()['history']:
        while result.is_chance_node() and not result.is_terminal():result.apply_action(deck[2*n+len(result.audit()['board'])])
        result.apply_action(history_action(entry))
    while result.is_chance_node() and not result.is_terminal():result.apply_action(deck[2*n+len(result.audit()['board'])])
    return result

class Joint:
    def __init__(self,native,game,decks,weights,max_nodes=10000,*,action_scope="allin",max_seconds=30):
        config=checked_config(game);self.game=game;self.N=game.num_players();self.W=len(decks);self.weights=np.array(weights,dtype=float)
        if action_scope not in ('allin','preflop') or type(max_nodes) is not int or not 1<=max_nodes<=100000 or type(max_seconds) not in (int,float) or not 0<max_seconds<=30:raise ValueError('explicit finite action/node/time scope')
        self.action_scope=action_scope
        if not decks or len(weights)!=len(decks) or self.weights.ndim!=1 or not np.all(np.isfinite(self.weights)) or np.any(self.weights<=0) or abs(self.weights.sum()-1)>1e-12:raise ValueError('explicit normalized finite chance law')
        if any(len(d)!=52 or any(type(c) is not int for c in d) or set(d)!=set(range(52)) for d in decks):raise ValueError('full disjoint52deck worlds')
        self.nodes=[];self.actions={};self.owners={};initial=[];begin=time.monotonic()
        for deck in decks:
            s=native.NativeState(game)
            for c in deck[:2*self.N]:s.apply_action(c)
            initial.append(s)
        def clone(s,w):
            from gto.qualification.range_continuation import history_action
            result=native.NativeState(game)
            for c in decks[w][:2*self.N]:result.apply_action(c)
            for entry in s.audit()['history']:
                while result.is_chance_node() and not result.is_terminal():result.apply_action(decks[w][2*self.N+len(result.audit()['board'])])
                result.apply_action(history_action(entry))
            while result.is_chance_node() and not result.is_terminal():result.apply_action(decks[w][2*self.N+len(result.audit()['board'])])
            return result
        def visit(states):
            if len(self.nodes)>=max_nodes or time.monotonic()-begin>max_seconds:raise ValueError('finite tree/time cap; nodes='+str(len(self.nodes)))
            for w,s in enumerate(states):
                while s.is_chance_node() and not s.is_terminal():s.apply_action(decks[w][2*self.N+len(s.audit()['board'])])
            k=len(self.nodes)
            if states[0].is_terminal():
                if not all(s.is_terminal() for s in states):raise ValueError('public terminal differs')
                self.nodes.append(dict(actor=-1,children=[],utility=np.array([s.returns() for s in states])/config['rules']['bb']));return k
            obs=[observation(s) for s in states];p=obs[0].actor;legal=obs[0].actions
            if any(o.actor!=p or o.actions!=legal or o.history!=obs[0].history for o in obs):raise ValueError('world public tree mismatch')
            acts=scoped_actions(obs[0],action_scope)
            keys=[o.key for o in obs]
            for key in keys:
                if key in self.actions and self.actions[key]!=acts:raise ValueError('infoset legal actions changed')
                self.actions[key]=acts;self.owners[key]=p
            self.nodes.append(dict(actor=p,actions=acts,keys=keys,children=[]))
            for a in acts:
                children=[clone(s,w) for w,s in enumerate(states)]
                for c in children:c.apply_action(a)
                self.nodes[k]['children'].append(visit(children))
            return k
        visit(initial);self.R={k:np.zeros(len(a)) for k,a in self.actions.items()};self.A={k:v.copy() for k,v in self.R.items()};self.t=0
        self.build_seconds=time.monotonic()-begin
        self.identity=dict(schema='native-finite-N-owner-joint-v1',config=config,decks=decks,weights=weights,source_sha256=sha(Path(__file__)),native_binary_sha256=sha(Path(native.__file__)),action_scope='native fold/maxlegalraise or all-in-call only' if action_scope=='allin' else 'native preflop fold/call/3BB/10BB/shove; explicit postflop check/call',formal_profile=False,ordinary_registry_admission=False)
    def policy(self,average=True):
        data=self.A if average else self.R
        return {k:(v/v.sum() if v.sum()>0 else np.ones(len(v))/len(v)) for k,v in data.items()}
    def reach(self,pi):
        r=[None]*len(self.nodes);r[0]=np.ones((self.W,self.N))
        for k,n in enumerate(self.nodes):
            if n['actor']<0:continue
            probs=np.array([pi[key] for key in n['keys']])
            for a,c in enumerate(n['children']):r[c]=r[k].copy();r[c][:,n['actor']]*=probs[:,a]
        return r
    def values(self,pi):
        v=[None]*len(self.nodes)
        for k in range(len(self.nodes)-1,-1,-1):
            n=self.nodes[k]
            if n['actor']<0:v[k]=n['utility'];continue
            probs=np.array([pi[key] for key in n['keys']]);v[k]=sum(probs[:,a,None]*v[c] for a,c in enumerate(n['children']))
        return v
    def step(self):
        pi=self.policy(False);reach=self.reach(pi);v=self.values(pi);self.t+=1
        grad={k:np.zeros_like(x) for k,x in self.R.items()}
        for k,n in enumerate(self.nodes):
            p=n['actor']
            if p<0:continue
            cf=self.weights*np.prod(reach[k][:,[i for i in range(self.N) if i!=p]],axis=1)
            for w,key in enumerate(n['keys']):
                grad[key]+=cf[w]*np.array([v[c][w,p]-v[k][w,p] for c in n['children']])
                self.A[key]+=self.t*self.weights[w]*reach[k][w,p]*pi[key]
        for key in self.R:self.R[key]=np.maximum(0,self.R[key]+grad[key])
    def br(self,pi,owner):
        reach=self.reach(pi);v=[None]*len(self.nodes)
        for k in range(len(self.nodes)-1,-1,-1):
            n=self.nodes[k]
            if n['actor']<0:v[k]=n['utility'][:,owner];continue
            if n['actor']!=owner:
                v[k]=sum(np.array([pi[key][a] for key in n['keys']])*v[c] for a,c in enumerate(n['children']));continue
            cf=self.weights*np.prod(reach[k][:,[i for i in range(self.N) if i!=owner]],axis=1);v[k]=np.zeros(self.W)
            for key in set(n['keys']):
                ws=[w for w,x in enumerate(n['keys']) if x==key];a=max(range(len(n['children'])),key=lambda a:sum(cf[w]*v[n['children'][a]][w] for w in ws))
                for w in ws:v[k][w]=v[n['children'][a]][w]
        return float(self.weights@v[0])
    def measure(self):
        pi=self.policy();ev=self.weights@self.values(pi)[0];br=[self.br(pi,p) for p in range(self.N)];gain=np.array(br)-ev
        if np.min(gain)<-1e-10:raise ValueError('BR below profile')
        return dict(iterations=self.t,players=self.N,nodes=len(self.nodes),infosets=len(pi),action_scope=self.identity['action_scope'],EV_bb=ev.tolist(),restricted_BR_bb=br,restricted_gain_bb=gain.tolist(),sum_restricted_unilateral_gains_bb=float(gain.sum()),full_native_BR_upper=None,full_native_NashConv=None,ordinary_registry_admission=False)
    def export(self,path):
        state=dict(identity=self.identity,t=self.t,R={k:v.tolist() for k,v in self.R.items()},A={k:v.tolist() for k,v in self.A.items()},actions={k:list(a) for k,a in self.actions.items()});state['digest']=digest(state);atomic(path,state);return state
    def restore(self,state):
        raw={k:v for k,v in state.items() if k!='digest'}
        if digest(raw)!=state['digest'] or state['identity']!=self.identity or state['actions']!={k:list(a) for k,a in self.actions.items()}:raise ValueError('finite game/state identity mismatch')
        for name in ('R','A'):
            if set(state[name])!=set(self.actions):raise ValueError('infoset state mismatch')
            arr={k:np.array(v,dtype=float) for k,v in state[name].items()}
            if any(x.shape!=self.R[k].shape or np.any(x<0) or not np.all(np.isfinite(x)) for k,x in arr.items()):raise ValueError('finite nonnegative regrets/averages')
            setattr(self,name,arr)
        if type(state['t']) is not int or not 0<=state['t']<=1000000:raise ValueError('finite iteration count')
        self.t=state['t']
    def profile(self):
        pi=self.policy();identity=digest(dict(game=self.identity,policy={k:v.tolist() for k,v in pi.items()}))
        def provider(o):
            if o.key not in pi:raise MissingResponse('outside finite joint-game support')
            return dict(zip(self.actions[o.key],pi[o.key].tolist()))
        return OfflineProfile(self.game,provider,players=self.N,provider_digest=identity)

def pure_br(q,pi,p):
    keys=[k for k in pi if q.owners[k]==p];choices=[range(len(pi[k])) for k in keys]
    if math.prod(map(len,choices))>65536:raise ValueError('pure oracle cap')
    best=-math.inf
    for selected in itertools.product(*choices):
        test={k:v.copy() for k,v in pi.items()}
        for k,a in zip(keys,selected):test[k]=np.eye(len(pi[k]))[a]
        def walk(k,w):
            node=q.nodes[k]
            if node['actor']<0:return node['utility'][w,p]
            return math.fsum(test[node['keys'][w]][a]*walk(c,w) for a,c in enumerate(node['children']))
        best=max(best,math.fsum(q.weights[w]*walk(0,w) for w in range(q.W)))
    return best

def diagnostic_decks(n):
    first=list(range(52));second=first.copy();second[:4]=first[2:4]+first[:2]
    return [first,second]

def expanded_decks(n):
    """Four actual different-payoff finite worlds, not a uniform52card model."""
    if type(n) is not int or not 3<=n<=9:raise ValueError('3..9 players')
    extras=[0,1,2,3,5,6,7,9,10,11,12,13][:2*(n-3)]
    designs=[([48,49,44,45,40,41],4),([48,49,44,45,40,41],46),
             ([48,49,40,41,44,45],42),([44,45,48,49,40,41],42)]
    decks=[]
    for hands,river in designs:
        prefix=hands+extras+[8,17,26,32,river]
        if len(prefix)!=len(set(prefix)):raise ValueError('blocked card reused')
        decks.append(prefix+[c for c in range(52) if c not in prefix])
    return decks

def terminal_paths(q,pi):
    """Independent exhaustive path products; never calls Joint.reach/values/br."""
    paths=[]
    def walk(k,w,history):
        node=q.nodes[k]
        if node['actor']<0:
            paths.append((w,history,node['utility'][w]));return
        p=node['actor'];key=node['keys'][w]
        for a,c in enumerate(node['children']):walk(c,w,history+((k,key,p,a,float(pi[key][a])),))
    for w in range(q.W):walk(0,w,())
    return paths

def path_oracle(q,pi):
    """Terminal-only CF products remove own past/current, retain future targets."""
    cf={k:np.zeros(len(p)) for k,p in pi.items()};avg={k:v.copy() for k,v in cf.items()}
    ev=np.zeros(q.N);seen=set()
    for w,path,u in terminal_paths(q,pi):
        ev+=q.weights[w]*math.prod(row[4] for row in path)*u
        for j,(k,key,p,a,prob) in enumerate(path):
            cf[key][a]+=q.weights[w]*math.prod(row[4] for i,row in enumerate(path) if row[2]!=p or i>j)*u[p]
            if (k,w) not in seen:
                seen.add((k,w));own=math.prod(row[4] for row in path[:j] if row[2]==p)
                avg[key]+=q.weights[w]*own*pi[key]
    grad={k:v-float(pi[k]@v) for k,v in cf.items()}
    return dict(EV=ev,grad=grad,avg=avg)

def path_br(q,pi,owner):
    """Optimize shared private/public plans AFTER hidden-world integration.

    Opponent/chance weights are terminal-path products. At each owner infoset,
    maximize a shared action, then sum observed successor infosets. This is
    independent of the vector-node BR recursion and excludes clairvoyant max.
    """
    records=[];prefixes={}
    for w,path,u in terminal_paths(q,pi):
        plan=tuple((key,a) for _,key,p,a,_ in path if p==owner)
        for j,(key,_) in enumerate(plan):
            if key in prefixes and prefixes[key]!=plan[:j]:raise ValueError('perfect recall violated')
            prefixes[key]=plan[:j]
        mass=q.weights[w]*math.prod(row[4] for row in path if row[2]!=owner)
        records.append((plan,mass*float(u[owner])))
    def best(records):
        total=0.;groups={}
        for plan,weighted in records:
            if not plan:total+=weighted
            else:groups.setdefault(plan[0][0],[]).append((plan,weighted))
        for key,rows in groups.items():
            total+=max(best([(plan[1:],v) for plan,v in rows if plan[0][1]==a]) for a in range(len(pi[key])))
        return total
    return best(records)

def run_expanded(build,out):
    from gto.qualification.build import load
    from gto.native.training import NativeGame
    _,native=load(build);out=Path(out);out.mkdir(parents=True,exist_ok=True);records=[];began=time.monotonic()
    for n in (3,6,9):
        game=NativeGame([24,22,20] if n==3 else [24-2*(p%3) for p in range(n)],
                        bba=0 if n==3 else 2,rake_num=0 if n==3 else 1,rake_den=20)
        start=time.monotonic()
        try:q=Joint(native,game,expanded_decks(n),[.25]*4,max_nodes=5000 if n==3 else 2000,
                    action_scope='preflop',max_seconds=30 if n==3 else 10)
        except ValueError as error:
            records.append(dict(players=n,status='BLOCKED_INCOMPLETE_TREE',reason=str(error),seconds=time.monotonic()-start,
                no_partial_policy_or_BR=True));atomic(out/'results.json',dict(records=records,verified_strategies=0,formal_acceptance=0));continue
        curve=[]
        for target in ((0,8,32) if n==3 else (0,8)):
            while q.t<target and time.monotonic()-start<30:q.step()
            measured=q.measure()
            if n==3:
                o=path_oracle(q,q.policy());error=max(abs(o['EV']-np.array(measured['EV_bb'])))
                error=max(error,max(abs(q.br(q.policy(),p)-path_br(q,q.policy(),p)) for p in range(n)))
                if error>1e-9:raise ValueError('independent hidden-world/path oracle mismatch')
                measured['independent_path_error_max']=error
            curve.append(measured)
        q.export(out/f'expanded-{n}max-checkpoint.json')
        records.append(dict(players=n,status='COMPLETE_FINITE_SCOPE_ONLY',build_seconds=q.build_seconds,
            seconds=time.monotonic()-start,curve=curve,full_native_BR_upper=None,full_native_NashConv=None,
            scope=q.identity['action_scope'],continuation_error_upper=None,omitted_action_error_upper=None))
        atomic(out/'results.json',dict(records=records,seconds=time.monotonic()-began,verified_strategies=0,formal_acceptance=0))
    return records

class SparseJoint:
    """SameN-owner CFR+ objective, sampled chance/opponents and sparseR/A.

    Finitepreflop actions/explicit postflopcheckcall only. Not a fullnativeNE
    certificate. Full-support opponentproposals also protect N-player averages.
    """
    def __init__(self,native,game,*,seed=17124101,decks=None,weights=None,epsilon=.2,
                 action_scope='preflop',max_nodes=20000,max_seconds=2,max_infosets=8000):
        config=checked_config(game)
        if (type(seed) is not int or type(epsilon) not in (int,float) or not 0<epsilon<=1
                or action_scope not in ('allin','preflop') or type(max_nodes) is not int or not 1<=max_nodes<=100000
                or type(max_seconds) not in (int,float) or not 0<max_seconds<=30
                or type(max_infosets) is not int or not 1<=max_infosets<=100000):raise ValueError('finite sparse N-owner budgets/proposal')
        if decks is None:
            if weights is not None:raise ValueError('full52law has no finiteweights')
            law=dict(kind='uniform52permutation-without-replacement')
            self.decks=None;self.weights=None
        else:
            w=np.array(weights,dtype=float)
            if (not decks or w.ndim!=1 or len(w)!=len(decks) or not np.all(np.isfinite(w))
                    or np.any(w<=0) or abs(w.sum()-1)>1e-12
                    or any(len(d)!=52 or any(type(c) is not int for c in d) or set(d)!=set(range(52)) for d in decks)):raise ValueError('normalized finite wholedecklaw')
            self.decks=tuple(tuple(d) for d in decks);self.weights=w.copy()
            law=dict(kind='explicitfiniteworlds',decks=[list(d) for d in decks],weights=w.tolist())
        self.native,self.game,self.N=native,game,game.num_players();self.epsilon=float(epsilon);self.action_scope=action_scope
        self.max_nodes,self.max_seconds,self.max_infosets=max_nodes,max_seconds,max_infosets
        self.rng=random.Random(seed);self.R={};self.A={};self.actions={};self.owners={};self.R_visits={};self.A_visits={};self.t=0;self.total_nodes=0
        self.identity=dict(schema='native-sparse-N-owner-external-v1',config=config,chance=law,epsilon=self.epsilon,
            action_scope=action_scope,seed=seed,schedule='onefrozenpi-for-allNowners/samechance/independentactionstreams',
            average='nonownerownreach/qprefix/(N-1),linear-time-weight',source_sha256=sha(Path(__file__)),
            native_binary_sha256=sha(Path(native.__file__)),formal_profile=False,ordinary_registry_admission=False)
    def policy(self,average=True):
        data=self.A if average else self.R
        return {k:(v/v.sum() if v.sum()>0 else np.ones(len(v))/len(v)) for k,v in data.items()}
    def _draw(self):
        if self.decks is None:return self.rng.sample(range(52),52)
        u=self.rng.random();total=0.
        for d,w in zip(self.decks,self.weights):
            total+=w
            if u<total:return list(d)
        return list(self.decks[-1])
    def collect(self,owner,deck,stream,pi,*,audit=False,budget=None):
        """Rawlinear estimators; audit enumeratesqchoices with their samplingmass."""
        if type(owner) is not int or not 0<=owner<self.N:raise ValueError('updating owner')
        if budget is None:budget=dict(nodes=0,start=time.monotonic())
        grads={};avgs={};acts={};owners={};maxavg=0.;maxscale=0.
        def add(dst,k,v):
            if k not in dst:dst[k]=np.zeros(len(v))
            dst[k]+=v
        def walk(state,logreach,logq,eventmass,stream):
            nonlocal maxavg,maxscale
            budget['nodes']+=1
            if budget['nodes']>self.max_nodes or time.monotonic()-budget['start']>self.max_seconds:raise ValueError('sparse node/timecap; incompletebatch')
            while state.is_chance_node() and not state.is_terminal():state.apply_action(deck[2*self.N+len(state.audit()['board'])])
            if state.is_terminal():
                values=np.array(state.returns(),dtype=float)/self.identity['config']['rules']['bb']
                if values.shape!=(self.N,) or not np.all(np.isfinite(values)):raise ValueError('finite N-dimensional nativeutility')
                return float(values[owner])
            o=observation(state);key=o.key;p=o.actor;actions=scoped_actions(o,self.action_scope)
            if key in self.actions and self.actions[key]!=actions:raise ValueError('sparse actionidentity changed')
            acts[key]=actions;owners[key]=p
            target=np.asarray(pi.get(key,np.ones(len(actions))/len(actions)),dtype=float)
            if target.shape!=(len(actions),) or not np.all(np.isfinite(target)) or np.any(target<0) or abs(target.sum()-1)>1e-12:raise ValueError('fixed normalized targetpolicy')
            if p==owner:
                values=[]
                for a,prob in zip(actions,target):
                    child=clone_native(self.native,self.game,deck,state);child.apply_action(a);r=logreach[:]
                    r[p]=r[p]+math.log(prob) if prob else -math.inf
                    values.append(walk(child,r,logq,eventmass,random.Random(stream.getrandbits(128))))
                value=float(target@values)
                scale=math.exp(math.fsum(logreach[i] for i in range(self.N) if i!=owner)-logq) if all(logreach[i]!=-math.inf for i in range(self.N) if i!=owner) else 0.
                maxscale=max(maxscale,scale);add(grads,key,eventmass*scale*(np.array(values)-value));return value
            weight=math.exp(logreach[p]-logq) if logreach[p]!=-math.inf else 0.
            maxavg=max(maxavg,weight);add(avgs,key,eventmass*weight*target)
            q=(1-self.epsilon)*target+self.epsilon/len(target)
            if audit:choices=[(j,float(q[j])) for j in range(len(q))]
            else:
                u=stream.random();j=int(np.searchsorted(np.cumsum(q),u,side='right'));j=min(j,len(q)-1);choices=[(j,1.)]
            value=0.
            for j,samplingmass in choices:
                child=clone_native(self.native,self.game,deck,state);child.apply_action(actions[j]);r=logreach[:]
                r[p]=r[p]+math.log(target[j]) if target[j] else -math.inf
                childvalue=walk(child,r,logq+math.log(q[j]),eventmass*samplingmass,
                    random.Random(stream.getrandbits(128)) if audit else stream)
                value+=samplingmass*target[j]/q[j]*childvalue
            return float(value)
        state=self.native.NativeState(self.game)
        for c in deck[:2*self.N]:state.apply_action(c)
        walk(state,[0.]*self.N,0.,1.,stream)
        if any(not np.all(np.isfinite(v)) for d in (grads,avgs) for v in d.values()):raise ArithmeticError('nonfinite sparse estimates; no clipping')
        return dict(grad=grads,avg=avgs,actions=acts,owners=owners,max_average_weight=maxavg,max_CF_scale=maxscale)
    def step(self):
        if checked_config(self.game)!=self.identity['config'] or self.epsilon!=self.identity['epsilon']:raise ValueError('sparse game/proposal config changed')
        if self.decks is not None and (self.weights.tolist()!=self.identity['chance']['weights'] or [list(d) for d in self.decks]!=self.identity['chance']['decks']):raise ValueError('sparse chance law changed')
        rngbefore=self.rng.getstate();pi=self.policy(False);budget=dict(nodes=0,start=time.monotonic());batches=[]
        try:
            deck=self._draw();seeds=[self.rng.getrandbits(128) for _ in range(self.N)]
            for owner in range(self.N):batches.append(self.collect(owner,deck,random.Random(seeds[owner]),pi,budget=budget))
            actions={};owners={};g={};avg={}
            for b in batches:
                for key,a in b['actions'].items():
                    if key in actions and actions[key]!=a:raise ValueError('batchinfoset actions changed')
                    actions[key]=a;owners[key]=b['owners'][key]
                for src,dst,scale in ((b['grad'],g,1.),(b['avg'],avg,1/(self.N-1))):
                    for key,v in src.items():
                        if key not in dst:dst[key]=np.zeros(len(v))
                        dst[key]+=scale*v
            if len(set(self.actions)|set(actions))>self.max_infosets:raise ValueError('sparse infosetcap; incompletebatch')
            newR={k:np.maximum(0,self.R.get(k,np.zeros(len(v)))+v) for k,v in g.items()}
            newA={k:self.A.get(k,np.zeros(len(v)))+(self.t+1)*v for k,v in avg.items()}
            if any(not np.all(np.isfinite(v)) for d in (newR,newA) for v in d.values()):raise ArithmeticError('sparse overflow; incompletebatch')
        except Exception:
            self.rng.setstate(rngbefore);raise
        for key,a in actions.items():
            if key not in self.actions:
                self.actions[key]=a;self.owners[key]=owners[key];self.R[key]=np.zeros(len(a));self.A[key]=np.zeros(len(a));self.R_visits[key]=0;self.A_visits[key]=0
        for key,v in newR.items():self.R[key]=v;self.R_visits[key]+=1
        for key,v in newA.items():self.A[key]=v;self.A_visits[key]+=int(np.sum(avg[key])>0)
        self.t+=1;self.total_nodes+=budget['nodes']
        return dict(iteration=self.t,nodes=budget['nodes'],infosets=len(self.actions),max_average_weight=max(b['max_average_weight'] for b in batches),max_CF_scale=max(b['max_CF_scale'] for b in batches))
    def state(self):
        raw=dict(identity=self.identity,t=self.t,rng=self.rng.getstate(),total_nodes=self.total_nodes,
            actions={k:list(v) for k,v in self.actions.items()},owners=self.owners,
            R={k:v.tolist() for k,v in self.R.items()},A={k:v.tolist() for k,v in self.A.items()},R_visits=self.R_visits,A_visits=self.A_visits)
        return {**copy.deepcopy(raw),'digest':digest(raw)}
    def restore(self,state):
        raw={k:v for k,v in state.items() if k!='digest'}
        if digest(raw)!=state['digest'] or state['identity']!=self.identity:raise ValueError('sparse checkpoint identity/digest mismatch')
        actions={k:tuple(v) for k,v in state['actions'].items()}
        if len(actions)>self.max_infosets or set(actions)!=set(state['owners']) or type(state['t']) is not int or not 0<=state['t']<=1000000:raise ValueError('sparse statebounds')
        if (type(state['total_nodes']) is not int or state['total_nodes']<0
                or any(type(v) is not int or not 0<=v<self.N or json.loads(k).get('actor')!=v for k,v in state['owners'].items())
                or any(set(state[f])!=set(actions) or any(type(v) is not int or v<0 for v in state[f].values()) for f in ('R_visits','A_visits'))):raise ValueError('sparse owner/visit bounds')
        arrays={}
        for field in ('R','A'):
            if set(state[field])!=set(actions):raise ValueError('sparse rowset mismatch')
            arrays[field]={k:np.asarray(v,dtype=float) for k,v in state[field].items()}
            if any(v.shape!=(len(actions[k]),) or not np.all(np.isfinite(v)) or np.any(v<0) for k,v in arrays[field].items()):raise ValueError('sparse nonnegative finite rows')
        def tuples(v):return tuple(tuples(x) for x in v) if isinstance(v,list) else v
        rng=random.Random();rng.setstate(tuples(state['rng']))
        self.actions=actions;self.owners=dict(state['owners']);self.R=arrays['R'];self.A=arrays['A'];self.rng=rng;self.t=state['t'];self.total_nodes=state['total_nodes'];self.R_visits=dict(state['R_visits']);self.A_visits=dict(state['A_visits'])
    def export(self,path):
        from gto.qualification.variance_study import compressed
        path=Path(path)
        if path.exists():raise FileExistsError('fresh sparse checkpoint path required')
        state=self.state();compressed(path,state);return state
    @property
    def policy_digest(self):return digest(dict(identity=self.identity,average={k:v.tolist() for k,v in self.policy().items()}))
    def profile(self):
        pi=self.policy();identity=self.policy_digest
        def provider(o):
            actions=scoped_actions(o,self.action_scope);p=pi.get(o.key,np.ones(len(actions))/len(actions))
            if len(p)!=len(actions):raise ValueError('sparse frozen rowshape')
            return dict(zip(actions,p.tolist()))
        return OfflineProfile(self.game,provider,players=self.N,provider_digest=identity)

def run_sparse(build,out,reuse_dir=None):
    """Shortoperational pilots and fixed-policy evaluation, not NEadoption."""
    import gzip,resource
    from gto.qualification.build import load
    from gto.qualification.multiplayer_scope import replay
    from gto.native.training import NativeGame
    _,native=load(build);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if (out/'training.json').exists():raise FileExistsError('fresh sparse study directory required')
    began=time.monotonic();seeds=(17124101,17124102);finite=[];ds=expanded_decks(3);g3=NativeGame([24,22,20])
    reuse=Path(reuse_dir) if reuse_dir else None
    if reuse:
        import ast,hashlib,shutil
        old_source=(reuse/'source-before-controller-fix.py').read_text();new_source=Path(__file__).read_text()
        def class_source(text):return next(ast.get_source_segment(text,n) for n in ast.parse(text).body if isinstance(n,ast.ClassDef) and n.name=='SparseJoint')
        if class_source(old_source)!=class_source(new_source):raise ValueError('recovery class changed')
        atomic(out/'recovery.json',dict(source_sha256=sha(reuse/'source-before-controller-fix.py'),current_source_sha256=sha(Path(__file__)),same_SparseJoint_class_sha256=hashlib.sha256(class_source(new_source).encode()).hexdigest(),scope='only runcontroller NumPy scalar serialization fixed; R/A/RNG source class unchanged'))
    exact=Joint(native,g3,ds,[.25]*4,action_scope='preflop');prior3=exact.measure()
    for seed in (() if reuse and (reuse/'finite-three-player.json').exists() else seeds):
        s=SparseJoint(native,g3,seed=seed,decks=ds,weights=[.25]*4);start=time.monotonic();status='COMPLETE'
        try:
            while s.t<64 and time.monotonic()-start<5:s.step()
        except (ValueError,ArithmeticError) as error:status='STOP_CAP:'+str(error)
        pi={k:s.policy().get(k,np.ones(len(a))/len(a)) for k,a in exact.actions.items()}
        ev=exact.weights@exact.values(pi)[0];br=[path_br(exact,pi,p) for p in range(3)]
        finite.append(dict(seed=seed,iterations=s.t,status=status,seconds=time.monotonic()-start,EV_bb=ev.tolist(),restricted_BR_bb=br,
            sum_restricted_gains_bb=float(sum(br)-sum(ev)),initial_sum_restricted_gains_bb=prior3['sum_restricted_unilateral_gains_bb'],
            scope='same exact4world3playerfinitegame; independent privateplan pathBR'))
        s.export(out/f'finite-3max-{seed}.json.gz')
    if reuse and (reuse/'finite-three-player.json').exists():
        finite=json.loads((reuse/'finite-three-player.json').read_text())['rows']
        shutil.copyfile(reuse/'finite-three-player.json',out/'finite-three-player.json')
    else:atomic(out/'finite-three-player.json',dict(rows=finite,full_native_BR_upper=None,full_native_NashConv=None))
    trained={};records=[]
    for n in (6,9):
        game=NativeGame([100-20*(p%3) for p in range(n)],bba=2,rake_num=1,rake_den=20);trained[n]=[]
        for seed in seeds:
            s=SparseJoint(native,game,seed=seed);compute=0.;io=0.;start=time.monotonic();stats=[];status='COMPLETE_BUDGET';recovered=False
            previous=reuse/f'{n}max-{seed}-final.json.gz' if reuse else None
            if previous and previous.exists():
                state=json.loads(gzip.decompress(previous.read_bytes()));raw={k:v for k,v in state.items() if k!='digest'}
                if digest(raw)!=state['digest'] or {k:v for k,v in state['identity'].items() if k!='source_sha256'}!={k:v for k,v in s.identity.items() if k!='source_sha256'}:raise ValueError('recovery policy identity')
                raw['identity']=s.identity;raw['digest']=digest(raw);s.restore(raw);recovered=True;status='RECOVERED_PREVIOUS_STOP_CAP'
            while not recovered and s.t<64 and compute<3.:
                tick=time.monotonic()
                try:row=s.step()
                except (ValueError,ArithmeticError) as error:
                    compute+=time.monotonic()-tick;status='STOP_CAP_ROLLEDBACK:'+str(error);break
                compute+=time.monotonic()-tick;stats.append(row)
                if s.t==8:
                    tick=time.monotonic();s.export(out/f'{n}max-{seed}-step8.json.gz');io+=time.monotonic()-tick
            tick=time.monotonic();s.export(out/f'{n}max-{seed}-final.json.gz');io+=time.monotonic()-tick
            trained[n].append(s)
            records.append(dict(players=n,seed=seed,status=status,iterations=s.t,infosets=len(s.R),total_sampled_nodes=s.total_nodes,
                compute_seconds=compute,checkpoint_seconds=io,wall_seconds=time.monotonic()-start,
                positive_average_infosets=int(sum(v.sum()>0 for v in s.A.values())),R_revisit_rate=1-len([v for v in s.R_visits.values() if v])/max(1,sum(s.R_visits.values())),
                A_revisit_rate=1-len([v for v in s.A_visits.values() if v])/max(1,sum(s.A_visits.values())),
                max_average_weight=max((x['max_average_weight'] for x in stats),default=0),max_CF_scale=max((x['max_CF_scale'] for x in stats),default=0),
                peak_sampled_batch_nodes=max((x['nodes'] for x in stats),default=0),policy_digest=s.policy_digest,expanded_training=False,recovered_checkpoint=str(previous) if recovered else None,previous_compute_seconds=None if recovered else 0))
            atomic(out/'training.json',dict(rows=records,ordinary_registry_admission=False,verified_strategies=0))
            if sum(p.stat().st_size for p in out.iterdir() if p.is_file())>20*1024*1024:raise ValueError('QA20MiB cap')
    evaluations=[];E=80;delta=.001/E;nworld=256
    def interval(values,lo,hi):
        mean=math.fsum(values)/len(values);radius=(hi-lo)*math.sqrt(math.log(2/delta)/(2*len(values)))
        return dict(mean=mean,interval=[max(lo,mean-radius),min(hi,mean+radius)],n=len(values))
    for n,solvers in trained.items():
        game=solvers[0].game;prior=SparseJoint(native,game,seed=0);profiles=[prior]+solvers;before=[s.state()['digest'] for s in profiles]
        frozen=[s.profile() for s in profiles];positive=[set(k for k,v in s.A.items() if v.sum()>0) for s in profiles]
        usage=[dict(paths_untrained=0,strategic_preflop_decisions=0,untrained_strategic_preflop_decisions=0,first_untrained_seats=[0]*n) for _ in profiles]
        samples=[[] for _ in profiles];rakes=[[] for _ in profiles];master=random.Random(17124200+n);start=time.monotonic()
        for _ in range(nworld):
            if time.monotonic()-began>120:raise ValueError('sparse study120sec cap')
            deck=master.sample(range(52),52);tape=master.getrandbits(128)
            for i,base in enumerate(frozen):
                seen=[False]
                def provider(o):
                    if o.round==0 and len(scoped_actions(o,'preflop'))>1:
                        usage[i]['strategic_preflop_decisions']+=1
                        if o.key not in positive[i]:
                            usage[i]['untrained_strategic_preflop_decisions']+=1
                            if not seen[0]:usage[i]['first_untrained_seats'][o.actor]+=1
                            seen[0]=True
                    return base.response.provider(o)
                profile=OfflineProfile(game,provider,players=n,provider_digest=base.identity['provider_digest'])
                result=replay(native,game,profile,deck=deck,seed=tape)
                samples[i].append(np.array(result['net_chips'])/2);rakes[i].append(result['rake_chips']/2);usage[i]['paths_untrained']+=int(seen[0])
        total=sum(game.stacks)/2;measure=[]
        for i,s in enumerate(profiles):
            vector=[interval([v[p] for v in samples[i]],-game.stacks[p]/2,total-game.stacks[p]/2) for p in range(n)]
            usage[i]['untrained_path_rate']=usage[i]['paths_untrained']/nworld
            usage[i]['untrained_strategic_preflop_rate']=usage[i]['untrained_strategic_preflop_decisions']/max(1,usage[i]['strategic_preflop_decisions'])
            fold=[-vector[2]['interval'][1],-vector[2]['interval'][0]]
            measure.append(dict(name='prior' if i==0 else 'learned-'+str(seeds[i-1]),policy_digest=s.policy_digest,seat_EV_bb=vector,
                mean_rake_bb=sum(rakes[i])/nworld,coverage=usage[i],root_UTG_fold_gain_interval_bb=fold,
                unilateral_probe_scope='seat2rootfoldhasexactutility0; loweronly, notBR',full_native_BR_upper=None,full_native_NashConv=None))
        differences=[]
        for i in (1,2):
            differences.append(dict(seed=seeds[i-1],seat_EV_change_bb=[interval([a[p]-b[p] for a,b in zip(samples[i],samples[0])],-total,total) for p in range(n)],
                scope='all-seat profile sensitivity, not unilateraldeviation or BR'))
        if before!=[s.state()['digest'] for s in profiles]:raise ValueError('evaluation mutated sampledstate')
        evaluations.append(dict(players=n,worlds_per_profile=nworld,seed=17124200+n,seconds=time.monotonic()-start,profiles=measure,paired_vs_prior=differences,
            confidence_family=.999,events_budget=E,method='fixed-n Hoeffding, simultaneous seats/profile differences',
            any_significant_seat_EV_change=any(x['interval'][0]>0 or x['interval'][1]<0 for d in differences for x in d['seat_EV_change_bb']),ordinary_adoption=False,expanded_training=False))
        atomic(out/'native-evaluation.json',dict(rows=evaluations,ordinary_registry_admission=False,verified_strategies=0,formal_acceptance=0))
    atomic(out/'resources.json',dict(seconds=time.monotonic()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        QA_bytes=sum(p.stat().st_size for p in out.iterdir() if p.is_file()),no_automatic_restart=True))
    return records

def run(build,out):
    from gto.qualification.build import load
    from gto.native.training import NativeGame
    _,native=load(build);out=Path(out);out.mkdir(parents=True,exist_ok=True);rows=[]
    for n in (3,6,9):
        game=NativeGame([10]*n) if n==3 else NativeGame([10+2*(p%3) for p in range(n)],bba=2,rake_num=1,rake_den=20);q=Joint(native,game,diagnostic_decks(n),[.5,.5]);start=time.monotonic();curve=[]
        for stopat in (0,8,32):
            while q.t<stopat and time.monotonic()-start<30:q.step()
            m=q.measure();curve.append(m)
            if n==3:
                for p in range(n):
                    if abs(q.br(q.policy(),p)-pure_br(q,q.policy(),p))>1e-10:raise ValueError('independent pureBR mismatch')
        q.export(out/f'{n}max-checkpoint.json');rows.append(dict(players=n,curve=curve,seconds=time.monotonic()-start,scope='finite2world restrictedallin game; not fullnative solved profile'));atomic(out/'results.json',dict(rows=rows,formal_acceptance=0,verified_RFI=0,verified_3bet=0))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--out',required=True);p.add_argument('--expanded',action='store_true');a=p.parse_args();(run_expanded if a.expanded else run)(a.build,a.out)
