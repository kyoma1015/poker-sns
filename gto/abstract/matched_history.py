"""Actual-action-tree miniature, exact finite chance; no full-game GTO admission.

Native CF vectors are reused. Python path products and realized pure responses
are independent of the native payoff/regret recursion. Historical full-population
checkpoints are neither fabricated nor reset by this experiment.
"""
import argparse, copy, hashlib, itertools, json, math, shutil, time
from pathlib import Path
from gto.abstract import joint_reach as j, joint_stream as s, joint_vector as v, model
from gto.hand169 import hand_class
from gto.native.hand169_bridge import card_name

METHODS = ('vanilla', 'cfr_plus', 'dcfr')
PROTOCOL = Path('docs/qa/matched-history-20261116/PROTOCOL.md')

def card(name):
    return '23456789TJQKA'.index(name[0])*4+'cdhs'.index(name[1])

def worlds(rank_lib):
    result = []
    for board, sb, bb in itertools.product(('2c 3d 7h', '4c 5d 6h'), ('Ac 9d', 'Ac 8d'), ('Kh Ks', 'Qh Qs')):
        flop = [card(c) for c in board.split()]
        hands = [[card(c) for c in text.split()] for text in (sb, bb)]
        dead = set(flop+hands[0]+hands[1]); assert len(dead) == 7
        score = 0
        for turn, river in itertools.combinations([c for c in range(52) if c not in dead], 2):
            ranks = [model.rank(rank_lib, hand+flop+[turn, river]) for hand in hands]
            score += 2*(ranks[0]>ranks[1])+(ranks[0]==ranks[1])
        signals = [model.CLASSES.index(hand_class([card_name(c) for c in hand]))*8 for hand in hands]
        result.append({'flop':flop, 'signals':signals, 'mass':1/8, 'equity':score/1980,
                       'holes':hands, 'runout_count':990})
    return result

def policy(g, values):
    out = [0.]*len(values)
    for k, key, i in g['keys']:
        n = len(g['nodes'][k]['children']); row = [max(0., x) for x in values[i:i+n]]; z = math.fsum(row)
        out[i:i+n] = [x/z for x in row] if z else [1/n]*n
    return out

def python_oracle(g, pi):
    """Explicit complete-state values and separate own/opponent path products."""
    ns, ws = g['nodes'], g['worlds']; W = len(ws); S = len(pi)
    grad = [0.]*S; avg = [0.]*S; total = 0.
    for wi, w in enumerate(ws):
        values = [0.]*len(ns); r = [[1.,1.] for _ in ns]
        for k, n in enumerate(ns):
            for a, c in enumerate(n['children']):
                r[c] = r[k].copy(); r[c][n['actor']] *= pi[g['info'][k*W+wi]+a]
        for k in range(len(ns)-1,-1,-1):
            n = ns[k]
            if n['actor']<0: values[k] = n['c0']+n['c1']*w['equity']; continue
            i = g['info'][k*W+wi]; owner = n['actor']; sign = 1 if owner==0 else -1
            values[k] = math.fsum(pi[i+a]*values[c] for a,c in enumerate(n['children']))
            for a,c in enumerate(n['children']):
                grad[i+a] += w['mass']*r[k][1-owner]*sign*(values[c]-values[k])
                avg[i+a] += w['mass']*r[k][owner]*pi[i+a]
        total += w['mass']*values[0]
    return {'grad':grad, 'avg':avg, 'ev':total}

def pure_response(g, pi, owner):
    """Integrate opponent cards and future boards BEFORE each information-set max."""
    ns, ws = g['nodes'], g['worlds']; W = len(ws); r = [[1.]*W for _ in ns]; response = list(pi)
    for k,n in enumerate(ns):
        for a,c in enumerate(n['children']):
            r[c] = [r[k][w]*(pi[g['info'][k*W+w]+a] if n['actor']!=owner else 1.) for w in range(W)]
    values = [None]*len(ns)
    for k in range(len(ns)-1,-1,-1):
        n = ns[k]
        if n['actor']<0:
            values[k] = [(n['c0']+n['c1']*w['equity'])*(1 if owner==0 else -1) for w in ws]; continue
        if n['actor'] == owner:
            totals = {}
            for wi,w in enumerate(ws):
                row = totals.setdefault(g['info'][k*W+wi], [0.]*len(n['children']))
                for a,c in enumerate(n['children']): row[a] += w['mass']*r[k][wi]*values[c][wi]
            choices = {i:max(range(len(row)), key=row.__getitem__) for i,row in totals.items()}
            for i,a in choices.items(): response[i:i+len(n['children'])] = [float(a==b) for b in range(len(n['children']))]
            values[k] = [values[n['children'][choices[g['info'][k*W+wi]]]][wi] for wi in range(W)]
        else:
            values[k] = [math.fsum(pi[g['info'][k*W+wi]+a]*values[c][wi] for a,c in enumerate(n['children'])) for wi in range(W)]
    value = math.fsum(w['mass']*x for w,x in zip(ws,values[0]))
    realized = python_oracle(g,response)['ev']*(1 if owner==0 else -1)
    if abs(value-realized)>1e-10: raise ValueError('pure response realization mismatch')
    return response, value

class Kernel:
    def __init__(self, lib, g):
        self.lib, self.g = lib, g
        self.boards = sorted({tuple(w['flop']) for w in g['worlds']})
        self.codes = sorted({x for w in g['worlds'] for x in w['signals']})
        ns, self.base, self.rows, self.P, self.S, _ = s.layout(len(self.codes))
        assert ns == g['nodes']
        self.indices = []
        for k,key,i in g['keys']:
            if ns[k]['street']=='preflop': self.indices.append((k,key,i,None,self.base[k]+key[0]*len(ns[k]['children'])))
            else: self.indices.append((k,key,i,tuple(key[0]),self.base[k]+self.codes.index(key[1])*len(ns[k]['children'])))
    def __call__(self, pi):
        G = [0.]*len(pi); A = [0.]*len(pi); ev = 0.; T = len(self.codes)
        for board in self.boards:
            worlds = [w for w in self.g['worlds'] if tuple(w['flop'])==board]; weight = math.fsum(w['mass'] for w in worlds)
            values = [0.]*(2*T*T)
            for w in worlds:
                i,jj = [self.codes.index(x) for x in w['signals']]; at=2*(i*T+jj)
                values[at] += w['mass']/weight; values[at+1] += w['mass']*w['equity']/weight
            full = s.strategy([0.]*self.S,[0.]*self.S,self.rows,False)
            for k,key,i,b,at in self.indices:
                if b is None or b==board: full[at:at+len(self.g['nodes'][k]['children'])] = pi[i:i+len(self.g['nodes'][k]['children'])]
            out = s.block(self.lib,{'codes':self.codes},values,full,full)
            ev += weight*out['metrics'][0]
            for k,key,i,b,at in self.indices:
                if b is None or b==board:
                    for a in range(len(self.g['nodes'][k]['children'])):
                        G[i+a] += weight*out['grad'][at+a]; A[i+a] += weight*out['avg'][at+a]
        return {'grad':G,'avg':A,'ev':ev}

class Trainer:
    def __init__(self,g,kernel):
        self.g,self.kernel = g,kernel; self.R=[0.]*len(g['width']); self.S=self.R.copy(); self.t=0
    def state(self): return {'R':self.R.copy(),'S':self.S.copy(),'t':self.t}
    def restore(self,state): self.R=state['R'].copy();self.S=state['S'].copy();self.t=state['t']
    def average(self): return policy(self.g,self.S)
    def step(self,method):
        if method not in METHODS: raise ValueError('unregistered method')
        self.t+=1; t=self.t
        for owners in ((0,),(1,)) if method=='cfr_plus' else ((0,1),):
            out=self.kernel(policy(self.g,self.R))
            for k,key,i in self.g['keys']:
                if self.g['nodes'][k]['actor'] not in owners: continue
                for a in range(len(self.g['nodes'][k]['children'])):
                    at=i+a; r=self.R[at]+out['grad'][at]
                    self.R[at]=max(0.,r) if method=='cfr_plus' else r
                    self.S[at]+=(t if method=='cfr_plus' else 1)*out['avg'][at]
                    if method=='dcfr':
                        power=t**(1.5 if r>0 else 0); self.R[at]*=power/(power+1);self.S[at]*=(t/(t+1))**2

def measure(g, pi):
    ev=python_oracle(g,pi)['ev']; br=[pure_response(g,pi,p)[1] for p in (0,1)]
    error=max(abs(br[p]-j.independent_br(g,pi,p)) for p in (0,1))
    if error>1e-10:raise ValueError('independent pure BR mismatch')
    return {'nashconv_bb':math.fsum(br),'sb_gain_bb':br[0]-ev,'bb_gain_bb':br[1]+ev,'sb_ev_bb':ev,'independent_pure_br_error_bb':error}

def identity(g):
    files=[Path(__file__),PROTOCOL,Path(s.__file__),Path(v.__file__).with_suffix('.cc'),Path(j.__file__),Path(model.__file__)]
    repository=Path(__file__).resolve().parents[2]
    return hashlib.sha256(json.dumps({'game':{'nodes':g['nodes'],'worlds':g['worlds']},'sources':{p.resolve().relative_to(repository).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},sort_keys=True).encode()).hexdigest()

def checkpoint(path, trainer, game_id, method):
    data={'identity':game_id,'method':method,**trainer.state()}; temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data,sort_keys=True)+'\n');temporary.replace(path)

def resume(path, trainer, game_id, method):
    data=json.loads(Path(path).read_text())
    if data.get('identity')!=game_id or data.get('method')!=method or method not in METHODS:
        raise ValueError('checkpoint game/source/method mismatch')
    if type(data.get('t')) is not int or data['t']<0 or any(not isinstance(data.get(k),list) or len(data[k])!=len(trainer.R) or any(type(x) not in (int,float) or not math.isfinite(x) or (k=='S' and x<0) for x in data[k]) for k in ('R','S')):
        raise ValueError('finite actual regret/average history required')
    trainer.restore(data)

def run(directory,seconds=180):
    root=Path(directory);root.mkdir(parents=True,exist_ok=True); start=time.monotonic()
    def budget():
        if time.monotonic()-start>seconds: raise TimeoutError('finite small-game deadline; checkpoints retained')
        if shutil.disk_usage(root).free<2*1024**3: raise ValueError('2GiB reserve')
    budget(); rank=model.load(model.build(root/'rank')); ws=worlds(rank); lib=v.build(root/'vector'); cases=[]; errors=[]
    for weights in ((.5,.5),(.25,.75)):
        adjusted=copy.deepcopy(ws); boards=sorted({tuple(w['flop']) for w in ws})
        for w in adjusted:w['mass']=weights[boards.index(tuple(w['flop']))]/4
        g=j.prepare(s.layout(4)[0],adjusted); kernel=Kernel(lib,g); game_id=identity(g)
        pi=policy(g,[float((i*7)%11) for i in range(len(g['width']))]); native=kernel(pi); independent=python_oracle(g,pi)
        errors.append(max(abs(a-b) for key in ('grad','avg') for a,b in zip(native[key],independent[key])))
        if errors[-1]>1e-10 or abs(native['ev']-independent['ev'])>1e-10:raise ValueError('path/vector mismatch')
        for age in (4,32):
            teacher=Trainer(g,kernel)
            for _ in range(age):budget();teacher.step('cfr_plus')
            inherited=teacher.state(); initial=measure(g,teacher.average()); methods={}
            for method in METHODS:
                x=Trainer(g,kernel);x.restore(inherited);points=[]
                for step in range(1,129):
                    budget();x.step(method)
                    if step%32==0:checkpoint(root/f'{weights[0]}-{age}-{method}.json',x,game_id,method)
                    if step in (32,128):points.append({'additional_iterations':step,**measure(g,x.average())})
                methods[method]=points
            cases.append({'board_weights':weights,'teacher_iterations':age,'identity':game_id,'initial':initial,'methods':methods})
            print(json.dumps({'completed_case':len(cases),'seconds':time.monotonic()-start}),flush=True)
    eligible=[m for m in METHODS if m!='cfr_plus' and all(c['methods'][m][-1]['nashconv_bb']<.9*min(c['initial']['nashconv_bb'],c['methods']['cfr_plus'][-1]['nashconv_bb']) for c in cases)]
    return {'scope':'EXPLICIT8WORLDS_ACTUAL270NODE_TREE_NOT_FULL_POPULATION','worlds':ws,'max_vector_path_error':max(errors),'cases':cases,'eligible_small_followup_only':eligible,'full_population_started':False,'frozen_population_nashconv_bb':0.9321071527220774,'population_improvement':'UNMEASURED','normal_GTO_added':0,'formal_acceptance':[0,12],'inherited_average_semantics':'Actual linear teacher mass retained. Vanilla new mass weight1; DCFR discounts inherited mass too. Continuation variants, not a claim of textbook global averaging from iteration1.','wall_seconds':time.monotonic()-start}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,required=True);parser.add_argument('--seconds',type=int,default=180);args=parser.parse_args()
    result=run(args.directory,args.seconds);(args.directory/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
