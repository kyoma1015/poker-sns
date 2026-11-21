"""Causal public/private-prefix fullstreet joint CFR+; offline research only."""
import argparse,ctypes as C,gzip,itertools,json,math,random,resource,subprocess,time
from pathlib import Path
import numpy as np
from gto.abstract import model,joint_update_audit as toy,joint_history
from gto.qualification import joint_release as old
from gto.qualification.native_mccfr import digest,betting
from gto.qualification.policy import sha,hand,act
from gto.qualification.range_continuation import street_tree
from gto.qualification.preflop_reopt import matched_states
from gto.qualification.preflop_release_solver import tree,load_policy
from gto.qualification.variance_study import compressed
from gto.qualification.evaluate import atomic

PUBLIC=(0,1,3,7)
WEIGHTS=np.array([18304*40*36,18304*40*12,18304*9*48,3796*49*48],dtype=float)/(22100*49*48)

def build(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);target=directory/'fullstreet.so'
    subprocess.run(['c++','-std=c++17','-O3','-fno-fast-math','-ffp-contract=off','-shared','-fPIC',str(Path(__file__).with_name('fullstreet_core.cc')),'-o',str(target)],check=True)
    return load(target)

def load(path):
    lib=C.CDLL(str(Path(path).resolve()));lib.fs_eval.argtypes=[C.c_int]*5+[model.IP]*11+[model.DP]*10+[C.c_int,model.DP];lib.fs_eval.restype=C.c_int
    lib.fs_feature.argtypes=[model.IP,model.IP,C.c_int];lib.fs_feature.restype=C.c_int
    lib.fs_nuts.argtypes=[model.IP,model.IP];lib.fs_nuts.restype=C.c_int
    lib.fs_world.argtypes=[model.IP,model.IP,model.IP,C.POINTER(C.c_int8)];lib.fs_world.restype=C.c_int
    return lib

def texture(board):return int(len({c//4 for c in board})<len(board))
def public_code(board):return sum(texture(board[:n])<<(5-n) for n in (3,4,5) if len(board)>=n)

def signal(lib,own,board):
    f=lib.fs_feature(model.ints(own),model.ints(board),3) if len(board)>=3 else 0
    t=lib.fs_feature(model.ints(own),model.ints(board),4) if len(board)>=4 else 0
    r=lib.fs_nuts(model.ints(own),model.ints(board)) if len(board)==5 else 0
    return 8*hand(own)+4*f+2*t+r

def native_tree(rules):
    pre=tree(rules);states=matched_states(rules,pre);ns=[]
    def terminal(b):
        folded=any(b.folded);v=b.settle([0,0],True)['net'][0] if folded else b.live[0]
        return dict(actor=-1,children=[],round=b.round,c0=v/2 if folded else -v/2,c1=0. if folded else v)
    def post(b):
        sub,bs=street_tree(b)
        def visit(k):
            n=sub[k];x=bs[k];at=len(ns)
            if n['actor']<0:
                if not x.done:return post(x)
                ns.append(terminal(x));return at
            ns.append(dict(actor=n['actor'],children=[],round=x.round,native_prefix=[list(h[:3]) for h in x.history],native_actions=n['native_actions']));ns[at]['children']=[visit(c) for c in n['children']];return at
        return visit(0)
    def previsit(k):
        n=pre[k];at=len(ns)
        if n['actor']<0:
            if n['matched'] and not states[k].done:return post(states[k])
            ns.append(dict(actor=-1,children=[],round=0,c0=(-n['value']/2 if n['matched'] else n['value']/2),c1=n['value'] if n['matched'] else 0.));return at
        ns.append(dict(n,round=0,children=[]));ns[at]['children']=[previsit(c) for c in n['children']];return at
    previsit(0);return ns

class Game:
    def __init__(self,lib,nodes,blocks,classes=169,prior=None):
        self.lib,self.nodes,self.blocks,self.C=lib,nodes,blocks,classes;self.base=[];self.rows=[];self.P=0;self.prebase=[];S=0
        for k,n in enumerate(nodes):
            self.base.append(S if n['actor']>=0 else -1);self.prebase.append(self.P if n['actor']>=0 and n['round']==0 else -1)
            if n['actor']>=0:
                r=n['round'];count=len(n['children']);t=classes*(1<<(2*r));self.rows.append((S,t,count,k));S+=t*count
                if r==0:self.P+=t*count
        self.S=S;self.types=[len(b['codes']) for b in blocks]
        self.estimate_bytes=S*54+64*1024**2+sum(len(nodes)*t*8*5 for t in self.types)+sum(t*t*16 for t in self.types)
        if self.estimate_bytes>512*1024**2:raise MemoryError('512MiB working budget')
        self.prior=np.zeros(S,dtype=np.float32)
        for start,t,n,k in self.rows:self.prior[start:start+t*n]=1/n
        if prior is not None:self.prior[:]=prior
        self.R=np.asarray(self.prior,dtype=float)*1e-15;self.A=np.zeros(S);self.visits=np.zeros(S,dtype=np.uint16);self.t=0
        self.grad=np.zeros(S);self.avg=np.zeros(S);self.den=np.zeros(S);self.num=np.zeros(self.P);self.evden=np.zeros(self.P)
        self.use_blocks(blocks)
    def use_blocks(self,blocks):
        self.blocks=blocks;lib=self.lib;nodes=self.nodes;S=self.S
        self.types=[len(b['codes']) for b in blocks];co=np.cumsum([0]+self.types[:-1]);mo=np.cumsum([0]+[t*t for t in self.types[:-1]])
        self.static=[model.ints([n['actor'] for n in nodes]),model.ints([len(n['children']) for n in nodes]),model.ints([c for n in nodes for c in (n['children']+[-1]*4)[:4]]),model.ints([n['round'] for n in nodes]),model.ints(self.base),model.ints(self.prebase),model.ints([b['public'] for b in blocks]),model.ints(self.types),model.ints(co),model.ints(mo),model.ints([c for b in blocks for c in b['codes']])]
        M=np.concatenate([np.asarray(b['mass']).ravel()*b['weight'] for b in blocks]);E=np.concatenate([np.asarray(b['equity']).ravel() for b in blocks])
        if not np.all(np.isfinite(M)) or np.min(M)<0 or abs(M.sum()-1)>1e-10 or np.min(E)<0 or np.max(E)>1:raise ValueError('valid unweighted joint chance')
        self.M=model.doubles(M);self.E=model.doubles(E);self.c0=model.doubles([n.get('c0',0.) for n in nodes]);self.c1=model.doubles([n.get('c1',0.) for n in nodes])
    def policy(self,average=True):
        data=self.A if average else self.R;out=np.empty(self.S)
        for start,t,n,k in self.rows:
            a=data[start:start+t*n].reshape(t,n);z=a.sum(axis=1)[:,None];fallback=self.prior[start:start+t*n].reshape(t,n).astype(float);fallback/=fallback.sum(axis=1)[:,None]
            out[start:start+t*n]=np.divide(a,z,out=fallback.copy(),where=z>0).ravel()
        return out
    def evaluate_owner(self,pi,owner):
        result=(C.c_double*2)()
        ptr=lambda x:x.ctypes.data_as(model.DP)
        rc=self.lib.fs_eval(len(self.nodes),len(self.blocks),self.C,self.S,owner,*self.static,self.M,self.E,self.c0,self.c1,ptr(pi),ptr(self.grad),ptr(self.avg),ptr(self.den),ptr(self.num),ptr(self.evden),self.P,result)
        if rc:raise ValueError('causal CF backend '+str(rc))
        return list(result)
    def step(self):
        self.t+=1
        for owner in (0,1):
            self.evaluate_owner(self.policy(False),owner)
            for start,t,n,k in self.rows:
                if self.nodes[k]['actor']!=owner:continue
                sl=slice(start,start+t*n);np.add(self.R[sl],self.grad[sl],out=self.R[sl]);np.maximum(self.R[sl],0,out=self.R[sl]);self.A[sl]+=self.t*self.avg[sl];self.visits[sl]=np.minimum(65535,self.visits[sl].astype(np.uint32)+(self.den[sl]>0))
    def measure(self):
        pi=self.policy();scores=[];evs=[];action={}
        for owner in (0,1):
            ev,br=self.evaluate_owner(pi,owner);scores.append(br);evs.append(ev)
            for start,t,n,k in self.rows:
                if self.nodes[k]['round']==0 and self.nodes[k]['actor']==owner:action[str(k)]=np.divide(self.num[self.prebase[k]:self.prebase[k]+t*n],self.evden[self.prebase[k]:self.prebase[k]+t*n],out=np.zeros(t*n),where=self.evden[self.prebase[k]:self.prebase[k]+t*n]>0).tolist()
        if abs(sum(evs))>1e-8 or min(scores[0]-evs[0],scores[1]-evs[1])< -1e-8:raise ValueError('zero sum/BR mismatch')
        return dict(iterations=self.t,EV_bb=evs[0],BR_SB_bb=scores[0],BR_BB_bb=scores[1],restricted_NC_bb=sum(scores),action_EV_bb=action,estimated_working_bytes=self.estimate_bytes,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    def save(self,path):
        path=Path(path);temporary=path.with_suffix('.tmp.npz');np.savez_compressed(temporary,R=self.R,A=self.A,visits=self.visits,t=np.array(self.t));temporary.replace(path)
    def restore(self,path):
        d=np.load(path)
        if d['R'].shape!=(self.S,) or d['A'].shape!=(self.S,) or d['visits'].shape!=(self.S,):raise ValueError('checkpoint shape')
        self.R[:]=d['R'];self.A[:]=d['A'];self.visits[:]=d['visits'];self.t=int(d['t'])


def make_boards(seed,parent,held=False):
    rng=random.Random(seed);out=[];oldflops=parent['heldout_flops'] if held else parent['train_flops'];excluded={tuple(b) for b in parent['train_flops']+parent['heldout_flops']}
    for public in PUBLIC:
        if held or public in (0,7):flop=list(oldflops[int(public==7)])
        else:
            while True:
                flop=sorted(rng.sample(range(52),3))
                if not texture(flop) and tuple(flop) not in excluded:excluded.add(tuple(flop));break
        while True:
            more=rng.sample([c for c in range(52) if c not in flop],2);board=flop+more
            if public_code(board)==public:out.append(board);break
    return out

def fresh_boards(seed,excluded):
    rng=random.Random(seed);out=[];excluded={tuple(sorted(b[:3])) for b in excluded}
    for public in PUBLIC:
        while True:
            board=rng.sample(range(52),5);board[:3]=sorted(board[:3])
            if public_code(board)==public and tuple(board[:3]) not in excluded:out.append(board);excluded.add(tuple(board[:3]));break
    return out

def moment(lib,board,weight):
    holes=(C.c_int*(1081*2))();flags=(C.c_int*1081)();eq=(C.c_int8*(1081*1081))()
    if lib.fs_world(model.ints(board),holes,flags,eq)!=1081:raise ValueError('full board conditional chance')
    h=np.asarray(holes).reshape(1081,2);full=np.array([8*hand(tuple(map(int,p)))+int(f) for p,f in zip(h,flags)])
    codes,ids=np.unique(full,return_inverse=True);T=len(codes);indices=ids[:,None]*T+ids[None,:];e=np.asarray(eq).reshape(1081,1081);valid=e>=0
    counts=np.bincount(indices[valid],minlength=T*T).reshape(T,T);win=np.bincount(indices[valid],weights=e[valid]/2,minlength=T*T).reshape(T,T)
    if counts.sum()!=1070190:raise ValueError('exact card removal count')
    M=counts/counts.sum();E=np.divide(win,counts,out=np.full_like(win,.5),where=counts>0)
    if np.max(abs(M*E+(M*E).T-M))>1e-12:raise ValueError('showdown zero sum')
    return dict(board=board,public=public_code(board),codes=list(map(int,codes)),mass=M,equity=E,weight=float(weight))

def save_blocks(path,blocks):
    packet={}
    for i,b in enumerate(blocks):
        for key in ('mass','equity','codes','board','public','weight'):packet[key+str(i)]=np.asarray(b[key])
    target=Path(path);temp=target.with_suffix('.tmp.npz');np.savez_compressed(temp,**packet);temp.replace(target)

def load_blocks(path):
    f=np.load(path);out=[]
    for i in range(4):out.append(dict(mass=f['mass'+str(i)],equity=f['equity'+str(i)],codes=list(map(int,f['codes'+str(i)])),board=list(map(int,f['board'+str(i)])),public=int(f['public'+str(i)]),weight=float(f['weight'+str(i)])))
    return out

def projected_prior(game,parent,nuts=True):
    out=np.zeros(game.S,dtype=np.float32);known={(n['street'],tuple(tuple(h) for h in n['native_prefix'])):k for k,n in enumerate(parent['nodes']) if n['actor']>=0}
    for start,t,n,k in game.rows:
        node=game.nodes[k];r=node['round'];actions=node['native_actions'];a=actions.index(1);arr=out[start:start+t*n].reshape(t,n);arr[:,a]=1
        if r<2:
            key=('preflop' if r==0 else 'flop',tuple(tuple(h) for h in node['native_prefix']));oldk=known[key];at=parent['bases'][oldk]
            if r==0:arr[:]=np.array(parent['pre_policy'][at:at+169*n]).reshape(169,n)
            else:
                for pub in (0,1):arr[pub*338:(pub+1)*338]=np.array(parent['post_policy'][pub][at-parent['P']:at-parent['P']+338*n]).reshape(338,n)
        elif r==3 and nuts:
            raises=[(j,a) for j,a in enumerate(actions) if a>1]
            if raises:
                best=max(raises,key=lambda x:x[1])[0];arr[1::2]=0;arr[1::2,best]=1
    return out

def inspect_coverage(game):
    result={}
    for r in range(4):
        allocated=visited=revisited=supported=0
        for start,t,n,k in game.rows:
            if game.nodes[k]['round']!=r:continue
            visits=game.visits[start:start+t*n].reshape(t,n).max(axis=1);mass=game.A[start:start+t*n].reshape(t,n).sum(axis=1)
            allocated+=t;visited+=int((visits>0).sum());revisited+=int((visits>1).sum());supported+=int((mass>0).sum())
        result[str(r)]=dict(allocated=allocated,CF_visited=visited,CF_revisited=revisited,revisit_rate=revisited/visited if visited else 0,positive_average=supported)
    return result

def study_exact(lib,out):
    from gto.qualification.fullstreet_oracle import fixture,reference,pure_br,path_oracle
    cases=[dict(equity=joint_history.EQUITIES[0],future=False),dict(equity=joint_history.EQUITIES[1],future=False),dict(equity=joint_history.EQUITIES[0],future=True)];results=[]
    for case,config in enumerate(cases):
        q=fixture(lib,**config);curve=[]
        for stop in (0,16,64,256,1024):
            while q.t<stop:q.step()
            pi=q.policy();m=q.measure();bs=[pure_br(q,pi,p) for p in (0,1)]
            if abs(m['restricted_NC_bb']-sum(bs))>1e-12 or abs(m['EV_bb']-reference(q,pi))>1e-12:raise ValueError('complete BR oracle mismatch')
            curve.append(dict(iterations=stop,NC_bb=sum(bs),EV_bb=m['EV_bb']))
        for p in (0,1):
            q.evaluate_owner(pi,p)
            for actual,expect in zip((q.grad,q.avg,q.den),path_oracle(q,pi,p)):np.testing.assert_allclose(actual,expect,atol=1e-12)
        results.append(dict(case=case,future_hidden_until_river=config['future'],curve=curve,gate=curve[-1]['NC_bb']<.01 and curve[-1]['NC_bb']<curve[2]['NC_bb']<curve[0]['NC_bb']))
    atomic(out,dict(cases=results,gate=all(x['gate'] for x in results),formal_acceptance=0));return all(x['gate'] for x in results)

class Policy:
    def __init__(self,meta,pi,average_mass,lib,base):
        if meta['source_py_sha256']!=sha(Path(__file__)) or meta['source_cpp_sha256']!=sha(Path(__file__).with_name('fullstreet_core.cc')) or meta['binary_sha256']!=sha(Path(lib._name)):raise ValueError('fullstreet source/build mismatch')
        self.meta,self.pi,self.average_mass,self.lib,self.base=meta,pi,average_mass,lib,base;self.native,self.rules=base.native,base.rules
        self.nodes,self.bases=meta['nodes'],meta['bases'];self.known={(n['round'],tuple(tuple(h) for h in n['native_prefix'])):k for k,n in enumerate(self.nodes) if n['actor']>=0}
        self.stats={r:dict(queries=0,unlearned=0,offtree=0) for r in range(4)};self.cache={}
        self._digest=digest(dict(identity=meta,policy_sha256=__import__('hashlib').sha256(np.asarray(pi,dtype='<f8').tobytes()).hexdigest(),fallback=base.fallback.policy_digest))
    @property
    def policy_digest(self):return self._digest
    def _row(self,o,track=True):
        if len(o.live)!=2 or any(o.live[p]+o.remaining[p]!=100 for p in (0,1)) or any(o.dead):raise ValueError('isolated HU50 only')
        r=o.round;key=(o.own,o.board)
        if key not in self.cache:
            if len(self.cache)>4096:self.cache.clear()
            self.cache[key]=signal(self.lib,o.own,o.board)
        code=self.cache[key];k=self.known.get((r,tuple(tuple(h[:3]) for h in o.history)))
        if track:self.stats[r]['queries']+=1
        if k is None:
            if track:self.stats[r]['offtree']+=1
            if r==0:return self.base.fallback.row(o,True)
            raises=[a for a in o.actions if a>1];a=max(raises) if r==3 and code%2 and raises else 1
            if a not in o.actions:raise ValueError('legal fallback check/call unavailable')
            return [float(x==a) for x in o.actions]
        n=self.nodes[k];na=len(n['children']);group=public_code(o.board)>>(3-r);obs=code>>(3-r);start=self.bases[k]+(group*(169<<r)+obs)*na
        if track and self.average_mass[start:start+na].sum()==0:self.stats[r]['unlearned']+=1
        weights=dict(zip(n['native_actions'],self.pi[start:start+na]));row=[weights.get(a,0.) for a in o.actions]
        if abs(sum(row)-1)>1e-10 or any(x<0 for x in row):raise ValueError('normalized legal fullstreet policy')
        return row
    def row(self,o,average=False):return self._row(o)
    def posterior(self,o):
        # Actual same-policy Bayes range, own/public only. Not a separate resolver.
        from gto.qualification.public_response import observe
        from gto.qualification.range_continuation import history_action,HOLES
        out=[]
        for h in HOLES:
            if set(h).intersection(o.own+o.board):out.append(0.);continue
            b=betting(self.rules);weight=1.
            for entry in o.history:
                a=history_action(entry)
                if b.actor!=o.actor:
                    shown=o.board[:(0,3,4,5)[b.round]];past=observe(b,h,shown);weight*=self._row(past,False)[past.actions.index(a)]
                act(b,a)
            out.append(weight)
        z=math.fsum(out)
        if z<=0:raise ValueError('zero conditional support; unspecified belief')
        return [x/z for x in out]


def dump_policy(game,folder,identity,name):
    folder=Path(folder);array=folder/(name+'.npz');tmp=array.with_suffix('.tmp.npz');pi=game.policy();np.savez_compressed(tmp,pi=pi,average_mass=game.A);tmp.replace(array)
    meta=dict(identity,nodes=game.nodes,bases=game.base,classes=game.C,iterations=game.t,array_sha256=sha(array),ordinary_registry_admission=False,formal_acceptance=0)
    atomic(folder/(name+'.json'),meta);return meta

def read_policy(folder,lib,base,name='policy-final'):
    folder=Path(folder);meta=json.loads((folder/(name+'.json')).read_text());array=folder/(name+'.npz')
    if sha(array)!=meta['array_sha256']:raise ValueError('policy array integrity')
    d=np.load(array);return Policy(meta,d['pi'],d['average_mass'],lib,base)


def run(build_dir,out,library):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);lib=load(library)
    if not study_exact(lib,out/'exact.json'):raise ValueError('exact convergence gate failed')
    base=load_policy(build_dir,old.ARTIFACT);ns=native_tree(base.rules);curves=[]
    for seed,parentseed in ((17120101,17119201),(17120102,17119202)):
        folder=out/str(seed);folder.mkdir(exist_ok=True);parentpath=Path('docs/qa/joint-release-20261119')/str(parentseed)/'policy-final.json.gz';parent=json.loads(gzip.decompress(parentpath.read_bytes()));cpfile=parentpath.with_name('checkpoint.json.gz');cp=json.loads(gzip.decompress(cpfile.read_bytes()));oldheld=np.array(cp['heldout'][0]['mass']).sum(axis=1)>0;oldstate=cp['state'];del cp
        for n in parent['nodes']:
            if n['actor']<0:continue
            k=parent['nodes'].index(n);at=parent['bases'][k];na=len(n['children']);t=169 if n['street']=='preflop' else 338
            if t==169:
                a=np.array(oldstate['A'][at:at+t*na]).reshape(t,na);z=a.sum(axis=1)[:,None];pi=np.divide(a,z,out=np.full_like(a,1/na),where=z>0);np.testing.assert_array_equal(pi.ravel(),parent['pre_policy'][at:at+t*na])
            else:
                for b in range(2):
                    x=at-parent['P'];a=np.array(oldstate['posts'][b][1][x:x+t*na]).reshape(t,na);z=a.sum(axis=1)[:,None];pi=np.divide(a,z,out=np.full_like(a,1/na),where=z>0);np.testing.assert_array_equal(pi.ravel(),parent['post_policy'][b][x:x+t*na])
        del oldstate
        trainboards=make_boards(seed,parent['identity']);diagboards=make_boards(seed+100,parent['identity'],True);fresh=fresh_boards(seed+10000,trainboards+diagboards+parent['identity']['train_flops']+parent['identity']['heldout_flops'])
        sets={}
        for name,boards in [('train',trainboards),('paired_comparison',diagboards),('fresh_heldout',fresh)]:
            blocks=[moment(lib,b,w) for b,w in zip(boards,WEIGHTS)];save_blocks(folder/(name+'.npz'),blocks);sets[name]=blocks
        q=Game(lib,ns,sets['train']);prior=projected_prior(q,parent,True);q.prior[:]=prior;q.R[:]=np.asarray(prior,dtype=float)*1e-15;del prior
        baseline=projected_prior(q,parent,False).astype(float);q.use_blocks(sets['fresh_heldout']);oldmetrics=[]
        for owner in (0,1):oldmetrics.append(q.evaluate_owner(baseline,owner))
        oldNC=sum(x[1] for x in oldmetrics);del baseline;q.use_blocks(sets['train'])
        identity=dict(schema='causal-fullstreet-CFR-plus-v1',source_py_sha256=sha(Path(__file__)),source_cpp_sha256=sha(Path(__file__).with_name('fullstreet_core.cc')),binary_sha256=sha(Path(lib._name)),parent_checkpoint_sha256=sha(cpfile),parent_policy_digest=parent['policy_digest'],inherited_regret_epochs=0,warmstart='old verified average behavior; fresh R=epsilon*float32prior,S=0; rivernuts legal prior',prior_precision_bits=32,seed=seed,train_boards=trainboards,fresh_heldout_boards=fresh,paired_comparison_boards=diagboards,public_weights=WEIGHTS.tolist(),formal_profile=False,classes=169)
        start=time.monotonic();dump_policy(q,folder,identity,'policy-initial')
        projected={c>>2 for b in sets['train'] if b['public']<4 for c in b['codes']};missing=sum(bool(x) and i not in projected for i,x in enumerate(oldheld))
        for stop in (0,16,64,128):
            while q.t<stop and time.monotonic()-start<180:q.step()
            q.use_blocks(sets['train']);tr=q.measure();q.use_blocks(sets['fresh_heldout']);he=q.measure();q.use_blocks(sets['paired_comparison']);co=q.measure();q.use_blocks(sets['train'])
            row=dict(seed=seed,iterations=q.t,train_NC_bb=tr['restricted_NC_bb'],fresh_heldout_NC_bb=he['restricted_NC_bb'],paired_comparison_NC_bb=co['restricted_NC_bb'],old_joint_fresh_NC_bb=oldNC,seconds=time.monotonic()-start,estimated_working_bytes=q.estimate_bytes,peak_RSS_bytes=he['peak_RSS_bytes'],old_heldout_flop_signals_absent_from_new_train=int(missing))
            q.save(folder/'checkpoint.npz');atomic(folder/'checkpoint.json',dict(identity,state_sha256=sha(folder/'checkpoint.npz'),iterations=q.t,nodes=ns,bases=q.base,train_file_sha256=sha(folder/'train.npz'),coverage=inspect_coverage(q)))
            meta=dump_policy(q,folder,identity,'policy-final');atomic(folder/'metrics.json',dict(train=tr,heldout=he,paired_comparison=co,old_joint_fresh_NC_bb=oldNC,coverage=inspect_coverage(q)))
            curves.append(row);atomic(out/'curves.json',dict(curves=curves,formal_acceptance=0));print(json.dumps(row),flush=True)
            if q.t<stop or (q.t>=64 and he['restricted_NC_bb']>=oldNC):break
        del q,parent,sets
    return curves

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--out',required=True);p.add_argument('--library',default='/tmp/fullstreet-build/fullstreet.so');a=p.parse_args();run(a.build,a.out,a.library)
