"""Matched-history tiny diagnostics. Never poker accuracy or production data."""
import copy,json
from unittest.mock import patch
from gto.abstract import joint_history as h

def run():
    cases=[]
    for game,equity in enumerate(h.EQUITIES):
        with patch.object(h.game,'EQUITY',equity):
            for age in (3,128):
                teacher=h.Trainer()
                for _ in range(age):teacher.step()
                state=teacher.state();initial=h.measure(teacher.average());methods={}
                for name,order,damping in [('alt_history','alternating',1.),('sim_history','simultaneous',1.),('alt_damp025','alternating',.25),('alt_damp05','alternating',.5),('alt_delayed','alternating',1.),('reset_regret_diagnostic','alternating',1.)]:
                    x=h.Trainer.restore(state)
                    if name=='reset_regret_diagnostic':x.R=[[0.]*16 for _ in range(2)]
                    points=[{'additional':0,**initial}];cut=None
                    for step in range(1,129):
                        x.step(order,damping)
                        if step==32:cut=copy.deepcopy(x.S)
                        if step in (32,64,128):
                            pi=x.average()
                            if name=='alt_delayed' and step>32:pi=[h.normalize([a-b for a,b in zip(s,c)],fallback) for s,c,fallback in zip(x.S,cut,x.behavior)]
                            points.append({'additional':step,**h.measure(pi)})
                    methods[name]={'points':points,'best':min(points,key=lambda x:x['nc']),'actual_regret_history_retained':name!='reset_regret_diagnostic','average_history_retained':True,'eligible_for_adoption':name!='reset_regret_diagnostic'}
                cases.append({'game':game,'teacher_actual_iterations':age,'initial':initial,'methods':methods})
    eligible=[]
    for name in ('sim_history','alt_damp025','alt_damp05','alt_delayed'):
        if all(c['methods'][name]['best']['nc']<.9*c['methods']['alt_history']['best']['nc'] and c['methods'][name]['best']['nc']<c['initial']['nc']-1e-9 for c in cases):eligible.append(name)
    return {'scope':'TWO EXPLICIT FINITE GAMES ONLY','cases':cases,'eligible_for_later_population_registration':eligible,'formal_acceptance':[0,12],'normal_GTO_added':0,'warning':'same optimization-game bestcheckpoint,not heldout or externalGTO;reset diagnostic NEVER eligible'}
if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
