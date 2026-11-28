"""Same-game preflop/flop CFR+ using the protected CF-vector kernel."""
import argparse,copy,ctypes as C,gzip,json,math,random,time
from pathlib import Path
import numpy as np
from gto.abstract import model,joint_vector,flop_exact,joint_update_audit as toy,joint_history
from gto.qualification.preflop_release_solver import tree,load_policy
from gto.qualification.preflop_reopt import matched_states,ARTIFACT
from gto.qualification.range_continuation import street_tree
from gto.qualification.policy import sha,hand,legal
from gto.qualification.native_mccfr import digest
from gto.qualification.variance_study import compressed
from gto.qualification.evaluate import atomic


def normalize(x,rows):
    out=np.zeros_like(x)
    for start,t,n,k in rows:
        a=x[start:start+t*n].reshape(t,n);z=a.sum(axis=1)[:,None]
        out[start:start+t*n]=np.divide(a,z,out=np.full((t,n),1/n),where=z>0).ravel()
    return out

class Trainer:
    def __init__(self,lib,nodes,pre_nodes,boundary,blocks,weights,classes=169,types=338):
        self.lib,self.nodes,self.pre_nodes,self.boundary=lib,nodes,pre_nodes,boundary
        self.blocks,self.weights,self.classes,self.types=blocks,weights,classes,types
        self.rows=[];self.base=[-1]*len(nodes);size=0;self.P=0
        for street in (0,1):
            for k,n in enumerate(nodes):
                if n['actor']>=0 and int(n['street']=='flop')==street:
                    t=types if street else classes;count=len(n['children']);self.base[k]=size;self.rows.append((size,t,count,k));size+=t*count
            if not street:self.P=size
        self.S=size;self.R=np.zeros(self.P);self.A=self.R.copy();self.posts=[(np.zeros(size-self.P),np.zeros(size-self.P)) for _ in blocks];self.t=0
        self.owner=np.zeros(size,dtype=int)
        for start,t,n,k in self.rows:self.owner[start:start+t*n]=nodes[k]['actor']
        self.static=[]
        for b in blocks:
            a=np.asarray(b['mass']);e=np.asarray(b['equity']);ii,jj=np.nonzero(a)
            # Zero-mass diagonal entries bind the class of every zero-support type.
            ii=np.concatenate([ii,np.arange(types)]);jj=np.concatenate([jj,np.arange(types)])
            mass=np.concatenate([a[ii[:-types],jj[:-types]],np.zeros(types)])
            eq=np.concatenate([e[ii[:-types],jj[:-types]],np.full(types,.5)])
            self.static.append((len(ii),*[model.ints(v) for v in ([int(x)//(types//classes) for x in ii],[int(x)//(types//classes) for x in jj],list(map(int,ii)),list(map(int,jj)))],model.doubles(mass),model.doubles(eq)))
        self.args=[model.ints([n['actor'] for n in nodes]),model.ints([len(n['children']) for n in nodes]),model.ints([c for n in nodes for c in (n['children']+[-1]*4)[:4]]),model.ints(self.base),model.ints([int(n['street']=='flop') for n in nodes]),model.ints(boundary)]
    def policy(self,b,average):
        r,a=self.posts[b];return normalize(np.concatenate([self.A,a]) if average else np.maximum(0,np.concatenate([self.R,r])),self.rows)
    def block(self,b,pi,override=None):
        # Optional moments change chance only; policy/layout remain identical.
        obj=self.static[b]
        if override is not None:
            other=Trainer(self.lib,self.nodes,self.pre_nodes,self.boundary,[override],[1.],self.classes,self.types);obj=other.static[0]
        W,*rest=obj;S=self.S;B=len(self.pre_nodes);grad=(C.c_double*S)();avg=(C.c_double*S)();leaf=(C.c_double*(2*B*169))();metric=(C.c_double*3)();num=(C.c_double*S)();den=(C.c_double*S)()
        rc=self.lib.stream_block(len(self.nodes),W,S,B,*self.args,*rest[:4],rest[4],rest[5],model.doubles([n.get('c0',0.) for n in self.nodes]),model.doubles([n.get('c1',0.) for n in self.nodes]),model.doubles(pi),grad,avg,leaf,metric,num,den)
        if rc:raise ValueError('joint vector block '+str(rc))
        return dict(grad=np.array(grad),avg=np.array(avg),leaf=np.array(leaf),metric=np.array(metric),num=np.array(num),den=np.array(den))
    def step(self):
        self.t+=1
        for owner in (0,1):
            pg=np.zeros(self.P);pa=pg.copy()
            for b,w in enumerate(self.weights):
                out=self.block(b,self.policy(b,False));pg+=w*out['grad'][:self.P];pa+=w*out['avg'][:self.P]
                r,a=self.posts[b];mask=self.owner[self.P:]==owner;r[mask]=np.maximum(0,r[mask]+w*out['grad'][self.P:][mask]);a[mask]+=self.t*w*out['avg'][self.P:][mask]
            mask=self.owner[:self.P]==owner;self.R[mask]=np.maximum(0,self.R[mask]+pg[mask]);self.A[mask]+=self.t*pa[mask]
    def measure(self,blocks=None,policies=None):
        B=len(self.pre_nodes);leaf=np.zeros(2*B*169);ev=0.;num=np.zeros(self.P);den=num.copy()
        for b,w in enumerate(self.weights):
            o=self.block(b,self.policy(b,True) if policies is None else policies[b],None if blocks is None else blocks[b]);leaf+=w*o['leaf'];ev+=w*o['metric'][0];num+=w*o['num'][:self.P];den+=w*o['den'][:self.P]
        br=[]
        for owner in (0,1):
            values={}
            for k in range(B-1,-1,-1):
                n=self.pre_nodes[k]
                if n['actor']<0:values[k]=leaf[(owner*B+k)*169:(owner*B+k)*169+self.classes]
                else:values[k]=(np.max if n['actor']==owner else np.sum)([values[c] for c in n['children']],axis=0)
            br.append(float(values[0].sum()))
        return dict(iterations=self.t,sb_EV_bb=ev,SB_BR_bb=br[0],BB_BR_bb=br[1],restricted_joint_NC_bb=sum(br),action_EV_bb=np.divide(num,den,out=np.zeros_like(num),where=den>0).tolist())
    def state(self):return dict(t=self.t,R=self.R.tolist(),A=self.A.tolist(),posts=[(r.tolist(),a.tolist()) for r,a in self.posts])
    def restore(self,state):
        self.t=state['t'];self.R=np.array(state['R']);self.A=np.array(state['A']);self.posts=[(np.array(r),np.array(a)) for r,a in state['posts']]


def tiny(lib,out):
    records=[]
    for case,eqs in enumerate(joint_history.EQUITIES):
        nodes=[dict(actor=a,children=c,street='flop' if k>=4 else 'preflop',c0=toy.C0[k],c1=toy.C1[k]) for k,(a,c) in enumerate(zip(toy.ACTOR,toy.CHILD))]
        pre=[dict(actor=0,children=[1,2]),dict(actor=-1,children=[]),dict(actor=1,children=[3,4]),dict(actor=-1,children=[]),dict(actor=-1,children=[])]
        bs=[dict(mass=np.asarray(toy.MASSES[b]).reshape(2,2).tolist(),equity=np.asarray(eqs[b]).reshape(2,2).tolist()) for b in range(2)]
        q=Trainer(lib,nodes,pre,[-1,1,-1,3,4,-1,-1,-1,-1],bs,toy.WEIGHT,2,2);curve=[]
        from unittest.mock import patch
        with patch.object(toy,'EQUITY',eqs):
            for stop in (0,16,64,256,1024):
                while q.t<stop:q.step()
                pi=[q.policy(b,True).tolist() for b in range(2)];measured=q.measure();direct=joint_history.measure(pi)
                if abs(measured['restricted_joint_NC_bb']-direct['nc'])>1e-12 or abs(measured['sb_EV_bb']-direct['ev'])>1e-12:raise ValueError('independent enumeration mismatch')
                curve.append(dict(iterations=stop,NC_bb=direct['nc'],EV_bb=direct['ev']))
            clone=Trainer(lib,nodes,pre,[-1,1,-1,3,4,-1,-1,-1,-1],bs,toy.WEIGHT,2,2);clone.restore(q.state());q.step();clone.step()
            if q.state()!=clone.state():raise ValueError('resume mismatch')
        records.append(dict(case=case,curve=curve,gate=curve[-1]['NC_bb']<.01 and curve[-1]['NC_bb']<curve[2]['NC_bb']<curve[0]['NC_bb']))
    atomic(out,dict(games=records,gate=all(r['gate'] for r in records),scope='existing exact2type2public-outcome game,all64 pure strategies/player',formal_acceptance=0))
    return all(r['gate'] for r in records)


def board_bucket(board):return int(len({c//4 for c in board[:3]})<3)

def own_flag(ranklib,own,flop):
    cards=list(own)+list(flop)
    return int(model.rank(ranklib,cards)//15**5>=1 or max(sum(c%4==s for c in cards) for s in range(4))>=4)

def native_tree(rules):
    pre=tree(rules);states=matched_states(rules,pre);nodes=[];boundary=[]
    def visit(k):
        n=pre[k];at=len(nodes)
        if n['actor']>=0:
            nodes.append(dict(n,street='preflop',pre_index=k,children=[]));boundary.append(-1)
            nodes[at]['children']=[visit(c) for c in n['children']]
        elif n['matched'] and not states[k].done:
            sub,bs=street_tree(states[k])
            for j,(x,b) in enumerate(zip(sub,bs)):
                common=dict(street='flop',native_prefix=[list(h[:3]) for h in b.history],native_actions=x.get('native_actions',[]),actor=x['actor'],children=[at+c for c in x['children']])
                if x['actor']<0:common.update(c0=-x['value']/2 if x['matched'] else x['value']/2,c1=x['value'] if x['matched'] else 0.)
                nodes.append(common);boundary.append(k if j==0 else -1)
        else:
            nodes.append(dict(actor=-1,children=[],street='preflop',c0=-n['value']/2 if n['matched'] else n['value']/2,c1=n['value'] if n['matched'] else 0.));boundary.append(k)
        return at
    visit(0);return nodes,pre,boundary

def sample_flops(seed):
    rng=random.Random(seed);out=[]
    for category in (0,1):
        while True:
            b=sorted(rng.sample(range(52),3))
            if board_bucket(b)==category:out.append(b);break
    return out

def moments(lib,ranklib,board,out):
    source=dict(board=board,flop_exact_sha=sha(Path(flop_exact.__file__)),matrix_sha=sha(Path(flop_exact.__file__).with_name('flop_exact_matrix.cc')),rank_sha=sha(Path(flop_exact.__file__).with_name('precision_native.cc')),feature='169class*2+madepair_or_fourflush_v1')
    path=Path(out)/(digest(source)+'.json.gz')
    if path.exists():
        d=json.loads(gzip.decompress(path.read_bytes()))
        if d['identity']!=source:raise ValueError('moment identity mismatch')
        return d
    start=time.monotonic();m=flop_exact.matrix(lib,board);h=np.asarray(m['pairs']);mask=(h[:,None,0]!=h[None,:,0])&(h[:,None,0]!=h[None,:,1])&(h[:,None,1]!=h[None,:,0])&(h[:,None,1]!=h[None,:,1])
    labels=np.asarray(m['labels']);flags=np.asarray([own_flag(ranklib,p,board) for p in m['pairs']]);codes=2*labels+flags;indices=codes[:,None]*338+codes[None,:]
    counts=np.bincount(indices[mask],minlength=338**2).reshape(338,338);win=np.asarray(m['win']).reshape(m['n'],m['n']);tie=np.asarray(m['tie']).reshape(m['n'],m['n'])
    weighted=np.bincount(indices[mask],weights=(win+.5*tie)[mask]/990,minlength=338**2).reshape(338,338)
    mass=counts/counts.sum();equity=np.divide(weighted,counts,out=np.full_like(weighted,.5),where=counts>0)
    if counts.sum()!=1271256 or np.max(abs(mass*equity+(mass*equity).T-mass))>1e-12:raise ValueError('physical chance/equity conservation')
    d=dict(identity=source,mass=mass.tolist(),equity=equity.tolist(),seconds=time.monotonic()-start,compatible_ordered_pairs=int(counts.sum()),runouts_per_pair=990)
    compressed(path,d);print(json.dumps(dict(moment_board=board,seconds=d['seconds'])),flush=True);return d

class JointPolicy:
    def __init__(self,artifact,base,ranklib):
        if artifact['identity']['source_sha256']!=sha(Path(__file__)) or artifact['identity']['rank_binary_sha256']!=sha(Path(ranklib._name)):raise ValueError('policy source/build identity mismatch')
        self.artifact,self.base,self.ranklib=artifact,base,ranklib;self.native,self.rules=base.native,base.rules
        self.nodes=artifact['nodes'];self.P=artifact['P'];self.pre=artifact['pre_policy'];self.post=artifact['post_policy'];self.bases=artifact['bases']
        self.known={(int(n['street']=='flop'),tuple(tuple(h) for h in n['native_prefix'])):k for k,n in enumerate(self.nodes) if n['actor']>=0}
        self._digest=digest(dict(identity=artifact['identity'],nodes=self.nodes,bases=self.bases,P=self.P,pre=self.pre,post=self.post,fallback=base.fallback.policy_digest))
        if artifact.get('policy_digest',self._digest)!=self._digest:raise ValueError('joint policy digest mismatch')
    @property
    def policy_digest(self):return self._digest
    def row(self,o,average=False):
        if any(o.live[p]+o.remaining[p]!=100 for p in (0,1)) or any(o.dead):raise ValueError('isolated HU50 zero-ante policy only')
        if o.round>=2:return self.base.row(o,True)
        k=self.known.get((o.round,tuple(tuple(h[:3]) for h in o.history)))
        if k is None:return self.base.fallback.row(o,True) if o.round==0 else self.base.row(o,True)
        node=self.nodes[k];actions=node['native_actions'];count=len(actions);c=hand(o.own)
        if o.round:
            c=2*c+own_flag(self.ranklib,o.own,o.board[:3]);i=self.bases[k]-self.P+c*count;row=self.post[board_bucket(o.board)][i:i+count]
        else:
            i=self.bases[k]+c*count;row=self.pre[i:i+count]
        if len(row)!=count or any(a not in o.actions for a in actions):raise ValueError('legal joint row required')
        weights=dict(zip(actions,row));return [weights.get(a,0.) for a in o.actions]

def passive_baseline(q,base):
    pi=np.zeros(q.S)
    for start,t,n,k in q.rows:
        node=q.nodes[k]
        if node['street']=='preflop':
            old=base.nodes[node['pre_index']];i=node['pre_index']
            for c in range(169):
                for a in range(n):pi[start+c*n+a]=base.strategy[(i*3+a)*169+c]
        else:
            a=node['native_actions'].index(1)
            for c in range(t):pi[start+c*n+a]=1
    return [pi.copy() for _ in q.blocks]

def train_hu(build,ranklib_path,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);lib=joint_vector.build(out/'build');ranklib=model.load(ranklib_path)
    if not tiny(lib,out/'tiny.json'):raise ValueError('exact gate failed; no HU50')
    base=load_policy(build,ARTIFACT);nodes,pre,bound=native_tree(base.rules);flib=flop_exact.build(out/'matrix-build');cache=out/'moments';cache.mkdir(exist_ok=True);weights=[18304/22100,3796/22100];curves=[]
    for seed in (17119201,17119202):
        folder=out/str(seed);folder.mkdir(exist_ok=True)
        trainboards=sample_flops(seed);heldboards=sample_flops(seed+100);bs=[moments(flib,ranklib,b,cache) for b in trainboards];held=[moments(flib,ranklib,b,cache) for b in heldboards]
        q=Trainer(lib,nodes,pre,bound,bs,weights);start=time.monotonic();identity=dict(schema='same-game-joint-native-flop-v1',seed=seed,train_flops=trainboards,heldout_flops=heldboards,board_weights=weights,
            preflop_raise_to_bb=[3,10,50],stacks_bb=[50,50],ante=0,rake=0,public_abstraction='paired/unpaired',private_abstraction='169class+currentpair/fourflush',turn_river='check-through',source_sha256=sha(Path(__file__)),vector_binary_sha256=sha(Path(lib._name)),rank_binary_sha256=sha(Path(ranklib._name)),formal_profile=False)
        baseline=q.measure(held,passive_baseline(q,base));last=None
        for stop in (0,16,64,128):
            while q.t<stop and time.monotonic()-start<180:q.step()
            current=q.measure();hold=q.measure(held);row=dict(seed=seed,iterations=q.t,train_NC_bb=current['restricted_joint_NC_bb'],heldout_NC_bb=hold['restricted_joint_NC_bb'],heldout_EV_bb=hold['sb_EV_bb'],baseline_heldout_NC_bb=baseline['restricted_joint_NC_bb'],seconds=time.monotonic()-start)
            compressed(folder/'checkpoint.json.gz',dict(identity=identity,state=q.state(),nodes=nodes,pre_nodes=pre,boundary=bound,train=bs,heldout=held))
            artifact=dict(identity=identity,nodes=nodes,pre_nodes=pre,P=q.P,bases=q.base,pre_policy=q.policy(0,True)[:q.P].tolist(),post_policy=[q.policy(b,True)[q.P:].tolist() for b in range(2)],iterations=q.t,train_metrics=current,heldout_metrics=hold,baseline_heldout_metrics=baseline,status='BLOCKED_UNVERIFIED',ordinary_registry_admission=False,verified_strategies=0,formal_acceptance=0)
            policy=JointPolicy(artifact,base,ranklib);artifact['policy_digest']=policy.policy_digest;row['policy_digest']=policy.policy_digest;compressed(folder/f'policy-{q.t}.json.gz',artifact);last=artifact;curves.append(row);atomic(out/'hu-curves.json',dict(curves=curves,formal_acceptance=0));print(json.dumps(row),flush=True)
            if q.t<stop or (q.t>=64 and hold['restricted_joint_NC_bb']>=baseline['restricted_joint_NC_bb']):break
        compressed(folder/'policy-final.json.gz',last)
    return curves

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--build');p.add_argument('--ranklib',default='/tmp/range-continuation-build/range.so');a=p.parse_args()
    if a.build:train_hu(a.build,a.ranklib,a.out)
    else:
        out=Path(a.out);out.mkdir(parents=True,exist_ok=True);tiny(joint_vector.build(out/'build'),out/'tiny.json')
