"""N-owner CFR+ in an explicit finite native all-in/fold/call research game.

Utilities remain N-dimensional, including rake. Restricted unilateral gains are
NOT fullnative NashConv, and multiplayer CFR has no HU minimax guarantee.
"""
import argparse,itertools,json,math,time
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

class Joint:
    def __init__(self,native,game,decks,weights,max_nodes=10000):
        config=checked_config(game);self.game=game;self.N=game.num_players();self.W=len(decks);self.weights=np.array(weights,dtype=float)
        if not decks or len(weights)!=len(decks) or np.any(self.weights<=0) or abs(self.weights.sum()-1)>1e-12:raise ValueError('explicit normalized finite chance law')
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
            if len(self.nodes)>=max_nodes or time.monotonic()-begin>30:raise ValueError('finite tree/time cap')
            for w,s in enumerate(states):
                while s.is_chance_node() and not s.is_terminal():s.apply_action(decks[w][2*self.N+len(s.audit()['board'])])
            k=len(self.nodes)
            if states[0].is_terminal():
                if not all(s.is_terminal() for s in states):raise ValueError('public terminal differs')
                self.nodes.append(dict(actor=-1,children=[],utility=np.array([s.returns() for s in states])/config['rules']['bb']));return k
            obs=[observation(s) for s in states];p=obs[0].actor;legal=obs[0].actions
            if any(o.actor!=p or o.actions!=legal or o.history!=obs[0].history for o in obs):raise ValueError('world public tree mismatch')
            acts=tuple(a for a in legal if a==0 or a==max(legal));keys=[o.key for o in obs]
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
        self.identity=dict(schema='native-finite-N-owner-joint-v1',config=config,decks=decks,weights=weights,source_sha256=sha(Path(__file__)),native_binary_sha256=sha(Path(native.__file__)),action_scope='native fold/maxlegalraise or all-in-call only',formal_profile=False,ordinary_registry_admission=False)
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
        return dict(iterations=self.t,players=self.N,nodes=len(self.nodes),infosets=len(pi),EV_bb=ev.tolist(),restricted_BR_bb=br,restricted_gain_bb=gain.tolist(),sum_restricted_unilateral_gains_bb=float(gain.sum()),full_native_BR_upper=None,full_native_NashConv=None,ordinary_registry_admission=False)
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
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.build,a.out)
