"""Registered tiny-game averaging study. No NLHE accuracy claim."""
import copy,json
from unittest.mock import patch
from gto.abstract import joint_history as h

def run():
    games=[]
    for equity in h.EQUITIES:
        with patch.object(h.game,'EQUITY',equity):
            teacher=h.Trainer()
            for _ in range(128):teacher.step()
            state=teacher.state();baseline=teacher.average();base=h.measure(baseline);candidates={}
            for name in ('full_history','delayed_output33','damping05','mixture25'):
                x=h.Trainer.restore(state);cut=None;points=[]
                for step in range(1,129):
                    x.step('alternating',.5 if name=='damping05' else 1.)
                    if step==32:cut=copy.deepcopy(x.S)
                    if step not in (32,64,128):continue
                    pi=x.average()
                    if name=='delayed_output33' and step>32:
                        pi=[h.normalize([a-b for a,b in zip(s,c)],fallback) for s,c,fallback in zip(x.S,cut,x.behavior)]
                    if name=='mixture25':pi=h.realization_mix(baseline,pi,.25)
                    points.append({'additional_iterations':step,**h.measure(pi)})
                candidates[name]={'points':points,'best_same_game_checkpoint':min(points,key=lambda p:p['nc']),'history_retained':True}
            control=candidates['full_history']['points'][-1]['nc']
            gates={name:c['points'][-1]['nc']<=.9*control and c['points'][-1]['nc']<base['nc'] for name,c in candidates.items() if name!='full_history'}
            games.append({'baseline':base,'candidates':candidates,'gate':gates})
    return {'scope':'TWO FINITE GAMES ONLY','games':games,'eligible_candidates':[name for name in games[0]['gate'] if all(g['gate'][name] for g in games)],'normal_GTO_added':0,'formal_acceptance':[0,12],'selection_warning':'optimization-game selection,not external or held-out validation'}

if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
