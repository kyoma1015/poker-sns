"""Matched-history/horizon tiny diagnostics; NOT heldout poker accuracy."""
import copy,json
from unittest.mock import patch
from gto.abstract import joint_history as h

METHODS=('alt_history','sim_history','alt_damp025','alt_damp05','alt_delayed','post_only','pre_only','post_then_full','reset_regret_diagnostic')

def scoped_step(x,scope):
    x.t+=1
    for owner in (0,1):
        pi=copy.deepcopy(x.behavior);outs=[h.game.oracle(b,p) for b,p in enumerate(pi)]
        sharedG=[sum(h.game.WEIGHT[b]*outs[b]['grad'][j] for b in range(2)) for j in range(8)];sharedA=[sum(h.game.WEIGHT[b]*outs[b]['avg'][j] for b in range(2)) for j in range(8)]
        for b in range(2):
            g=sharedG+[h.game.WEIGHT[b]*v for v in outs[b]['grad'][8:]];a=sharedA+[h.game.WEIGHT[b]*v for v in outs[b]['avg'][8:]]
            for j in range(16):
                if h.OWNER(j)!=owner:continue
                selected=scope=='all' or (scope=='pre')==(j<8)
                if selected:x.R[b][j]=max(0.,x.R[b][j]+g[j])
                x.S[b][j]+=x.t*a[j]
            target=h.normalize(x.R[b],[.5]*16)
            for j in range(16):
                if h.OWNER(j)==owner and (scope=='all' or (scope=='pre')==(j<8)):x.behavior[b][j]=target[j]

def run():
    cases=[]
    for game,equity in enumerate(h.EQUITIES):
        with patch.object(h.game,'EQUITY',equity):
            original=h.measure(h.game.policies())
            for age in (3,128):
                teacher=h.Trainer()
                for _ in range(age):teacher.step()
                state=teacher.state();initial=h.measure(teacher.average())
                for horizon in (4,128):
                    methods={};checkpoints=(1,2,4) if horizon==4 else (32,64,128)
                    for name in METHODS:
                        x=h.Trainer.restore(state)
                        if name=='reset_regret_diagnostic':x.R=[[0.]*16 for _ in range(2)]
                        points=[{'additional':0,**initial}];cut=None
                        for step in range(1,horizon+1):
                            if name in ('pre_only','post_only','post_then_full'):
                                scope='pre' if name=='pre_only' else ('post' if name=='post_only' or step<=horizon//2 else 'all');scoped_step(x,scope)
                            else:x.step('simultaneous' if name=='sim_history' else 'alternating',.25 if name=='alt_damp025' else (.5 if name=='alt_damp05' else 1.))
                            if step==horizon//4:cut=copy.deepcopy(x.S)
                            if step in checkpoints:
                                pi=x.average()
                                if name=='alt_delayed' and step>horizon//4:pi=[h.normalize([a-b for a,b in zip(s,c)],fallback) for s,c,fallback in zip(x.S,cut,x.behavior)]
                                points.append({'additional':step,**h.measure(pi)})
                        methods[name]={'points':points,'best':min(points,key=lambda p:p['nc']),'actual_initial_regret_history_retained':name!='reset_regret_diagnostic','average_history_retained':True,'future_regret_updates':'selected street only' if name in ('pre_only','post_only','post_then_full') else 'all','eligible_for_adoption':name!='reset_regret_diagnostic'}
                    cases.append({'game':game,'teacher_actual_iterations':age,'additional_budget':horizon,'protected_original_baseline':original,'initial':initial,'methods':methods})
    eligible=[]
    for name in METHODS:
        if name in ('alt_history','reset_regret_diagnostic'):continue
        if all(c['methods'][name]['best']['nc']<.9*c['methods']['alt_history']['best']['nc'] and c['methods'][name]['best']['nc']<min(c['initial']['nc'],c['protected_original_baseline']['nc'])-1e-9 for c in cases):eligible.append(name)
    return {'scope':'SAME TWO EXPLICIT FINITE FIXTURES,NOT NEW HELDOUT/HU50','cases':cases,'eligible_for_later_population_registration':eligible,'formal_acceptance':[0,12],'normal_GTO_added':0,'warning':'same optimization-game bestcheckpoint;initialhistories retained except labelled reset diagnostic. Scoped updates omit unselected newregrets,not standard fullCFR.'}
if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
