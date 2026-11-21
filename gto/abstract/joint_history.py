"""Independent tiny-game history/order/realization study. Not poker GTO data."""
import argparse,copy,hashlib,itertools,json,math
from pathlib import Path
from unittest.mock import patch
from gto.abstract import joint_update_audit as game

ROWS=tuple(range(0,16,2))
OWNER=lambda j:0 if j<4 or 8<=j<12 else 1
EQUITIES=(game.EQUITY,[[.9,.65,.3,.1],[.85,.6,.3,.05]])

def validate_policy(pi):
    if len(pi)!=2 or any(len(row)!=16 for row in pi):raise ValueError("policy shape")
    for row in pi:
        if any(not math.isfinite(x) or not 0<=x<=1 for x in row) or any(abs(sum(row[i:i+2])-1)>1e-12 for i in ROWS):raise ValueError("normalized legal policy")
    if any(abs(x-y)>1e-12 for x,y in zip(pi[0][:8],pi[1][:8])):raise ValueError("future-board information in preflop policy")

def normalize(values,fallback):
    out=[]
    for i in ROWS:
        z=math.fsum(values[i:i+2]);out.extend([v/z for v in values[i:i+2]] if z>0 else fallback[i:i+2])
    return out

def ev(pi):
    """Direct cashflow polynomial, separate from the recursive path oracle."""
    total=0.
    for b,h,v in itertools.product(range(2),repeat=3):
        w=2*h+v;e=game.EQUITY[b][w];p0=pi[b][2*h+1];p1=pi[b][4+2*v+1];p2=pi[b][8+2*h+1];p3=pi[b][12+2*v+1]
        u=(1-p0)*(-.5)+p0*((1-p1)+p1*((1-p2)*(-2+4*e)+p2*((1-p3)*2+p3*(-3+6*e))))
        total+=game.WEIGHT[b]*game.MASSES[b][w]*u
    return total

def measure(pi):
    validate_policy(pi)
    value=ev(pi);br=[game.brute_br(pi,p) for p in (0,1)];nc=math.fsum(br)
    if min(br[0]-value,br[1]+value,nc)<-1e-10:raise ValueError('independent BR signs')
    return {'nc':nc,'sb_gain':br[0]-value,'bb_gain':br[1]+value,'ev':value}

def own_masses(pi):
    validate_policy(pi)
    out=[game.oracle(b,p)['avg'] for b,p in enumerate(pi)]
    pre=[sum(game.WEIGHT[b]*out[b][j] for b in range(2)) for j in range(8)]
    return [pre+[game.WEIGHT[b]*v for v in out[b][8:]] for b in range(2)]

def realization_mix(left,right,weight):
    if not 0<=weight<=1:raise ValueError('convex mixture')
    x,y=own_masses(left),own_masses(right)
    return [normalize([(1-weight)*v+weight*w for v,w in zip(a,b)],fallback) for a,b,fallback in zip(x,y,left)]

class Trainer:
    def __init__(self,policy=None):
        pi=copy.deepcopy(policy or game.policies());validate_policy(pi);self.R=[[1e-15*x for x in p] for p in pi];self.S=[[0.]*16 for _ in range(2)];self.behavior=pi;self.t=0
    def state(self):return copy.deepcopy({'R':self.R,'S':self.S,'behavior':self.behavior,'t':self.t})
    @classmethod
    def restore(cls,state):
        obj=cls();obj.R=copy.deepcopy(state['R']);obj.S=copy.deepcopy(state['S']);obj.behavior=copy.deepcopy(state['behavior']);obj.t=state['t'];return obj
    def average(self):return [normalize(s,p) for s,p in zip(self.S,self.behavior)]
    def step(self,order='simultaneous',damping=1.):
        if order not in ('simultaneous','alternating') or not 0<damping<=1:raise ValueError('explicit order/damping')
        self.t+=1
        def stage(owners):
            pi=copy.deepcopy(self.behavior);outs=[game.oracle(b,p) for b,p in enumerate(pi)]
            sharedG=[sum(game.WEIGHT[b]*outs[b]['grad'][j] for b in range(2)) for j in range(8)]
            sharedA=[sum(game.WEIGHT[b]*outs[b]['avg'][j] for b in range(2)) for j in range(8)]
            for b in range(2):
                g=sharedG+[game.WEIGHT[b]*x for x in outs[b]['grad'][8:]];a=sharedA+[game.WEIGHT[b]*x for x in outs[b]['avg'][8:]]
                for j in range(16):
                    if OWNER(j) in owners:self.R[b][j]=max(0.,self.R[b][j]+g[j]);self.S[b][j]+=self.t*a[j]
                target=normalize(self.R[b],[.5]*16)
                for j in range(16):
                    if OWNER(j) in owners:self.behavior[b][j]=(1-damping)*pi[b][j]+damping*target[j]
        if order=='simultaneous':stage((0,1))
        else:
            for player in (0,1):stage((player,))

BITS=list(itertools.product(range(2),repeat=6))
def pure(owner,bits):
    pi=[[.5]*16 for _ in range(2)]
    for b,h in itertools.product(range(2),repeat=2):
        for start,index in [(0 if owner==0 else 4,h),(8 if owner==0 else 12,2+2*b+h)]:
            i=start+2*h;pi[b][i:i+2]=[int(bits[index]==0),int(bits[index]==1)]
    return pi

def lp_reference():
    import numpy as np
    from scipy.optimize import linprog
    profiles=[[pure(p,bits) for bits in BITS] for p in (0,1)]
    def pair(x,y):return [[x[b][j] if OWNER(j)==0 else y[b][j] for j in range(16)] for b in range(2)]
    matrix=np.asarray([[ev(pair(x,y)) for y in profiles[1]] for x in profiles[0]])
    a=linprog([0.]*64+[-1.],A_ub=np.column_stack((-matrix.T,np.ones(64))),b_ub=np.zeros(64),A_eq=[[1.]*64+[0.]],b_eq=[1.],bounds=[(0,None)]*64+[(None,None)],method='highs')
    b=linprog([0.]*64+[1.],A_ub=np.column_stack((matrix,-np.ones(64))),b_ub=np.zeros(64),A_eq=[[1.]*64+[0.]],b_eq=[1.],bounds=[(0,None)]*64+[(None,None)],method='highs')
    if not a.success or not b.success:raise ValueError('independent LP failed')
    gap=b.fun+a.fun
    pi=[[.5]*16 for _ in range(2)]
    for owner,solution in enumerate((a,b)):
        masses=[[[0.]*16 for _ in range(2)]][0]
        for probability,profile in zip(solution.x[:64],profiles[owner]):
            if probability<=0:continue
            own=own_masses(profile)
            for board in range(2):
                for j in range(16):masses[board][j]+=probability*own[board][j]
        for board in range(2):
            behavior=normalize(masses[board],[.5]*16)
            for j in range(16):
                if OWNER(j)==owner:pi[board][j]=behavior[j]
    metric=measure(pi)
    if gap>1e-8 or metric['nc']>1e-8:raise ValueError('LP and enumerated pureBR disagree')
    return {'value':-a.fun,'dual_gap':gap,'independent_br':metric,'policy':pi,'pure_strategies_per_player':64}

CANDIDATES={'sim_true':('simultaneous',True,True,1.),'alt_true':('alternating',True,True,1.),'alt_reset_R':('alternating',False,True,1.),'alt_reset_S':('alternating',True,False,1.),'alt_reset_both':('alternating',False,False,1.),'alt_damped_experimental':('alternating',True,True,.25)}
CHECKPOINTS=(0,1,2,4,8,16,32,64,128)
def study(references=None):
    results=[]
    for case,equity in enumerate(EQUITIES):
        with patch.object(game,'EQUITY',equity):
            reference=lp_reference() if references is None else references[case]
            if measure(reference["policy"])["nc"]>1e-8 or abs(ev(reference["policy"])-reference["value"])>1e-8:raise ValueError("independent reference certificate failed")
            teacher=Trainer()
            for _ in range(128):teacher.step()
            state=teacher.state();baseline=teacher.average();initial=measure(baseline);candidates={}
            for name,(order,keepR,keepS,damping) in CANDIDATES.items():
                t=Trainer.restore(state)
                if not keepR:t.R=[[1e-15*x for x in p] for p in t.behavior]
                if not keepS:t.S=[[0.]*16 for _ in range(2)]
                points=[];best={'nc':initial['nc'],'additional_updates':0,'lambda':0.}
                for i in range(129):
                    if i in CHECKPOINTS:
                        pi=t.average();raw=measure(pi);mixtures=[]
                        for weight in (0.,.125,.25,.5,1.):
                            metric=measure(realization_mix(baseline,pi,weight));mixtures.append({'lambda':weight,**metric})
                            if metric['nc']<best['nc']-1e-9:best={'nc':metric['nc'],'additional_updates':i,'lambda':weight}
                        points.append({'additional_updates':i,**raw,'mixtures':mixtures})
                    if i<128:t.step(order,damping)
                candidates[name]={'genuine_inherited_regret_iterations':128 if keepR else 0,'genuine_inherited_average_iterations':128 if keepS else 0,'schedule_offset':128,'order':order,'damping':damping,'points':points,'best_on_same_optimization_game':best,'final_state':t.state()}
            sim=candidates['sim_true']['points'][-1]['nc'];alt=candidates['alt_true']['points'][-1]['nc']
            results.append({'equity':equity,'reference':reference,'actual_teacher_state':state,'baseline':initial,'candidates':candidates,'population_gate_pass':alt<=.75*sim and alt<initial['nc']-1e-9})
    return {'scope':'TWO TINY FINITE GAMES ONLY,NOT HU50 OR EXTERNAL GTO','games':results,'full_population_gate_pass':all(x['population_gate_pass'] for x in results),'formal_acceptance':[0,12],'normal_GTO':0,'warning':'best checkpoint/mixture selection uses this optimization game,not holdout evidence'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=study();a.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'gate':result['full_population_gate_pass'],'games':[{'baseline':g['baseline'],'final':{n:c['points'][-1]['nc'] for n,c in g['candidates'].items()}} for g in result['games']]}),flush=True)
