"""Normalize complete population research rows; never grant ordinary admission."""
import argparse,json,math
from pathlib import Path
from gto.abstract import model,fullsupport as fs

CONTEXTS={'rfi':[],'vs_open':['raise_to_5'],'vs_3bet':['raise_to_5','raise_to_18'],'vs_4bet':['raise_to_5','raise_to_18','raise_to_42']}

def export(result,*,normal=False):
    if normal:raise ValueError('formal conditions and real-game precision unverified; research only')
    if result['coverage']!=1 or result['evaluated_orbits']!=1755 or result['population_orbits']!=1755:raise ValueError('full physical population required; no partial-range export')
    pi=fs.unpack(result['preflop_frequency']);ev=result['preflop_action_ev_bb'];ranges=[]
    if len(pi)!=len(ev):raise ValueError('frequency/actionEV shape')
    for context,history in CONTEXTS.items():
        matches=[x for x in result['preflop_layout'] if x['history']==history]
        if len(matches)!=1:raise ValueError('exact public history required')
        row=matches[0];actions=row['actions'];n=len(actions);start=row['base']
        original=next(x for x in model.tree() if x['actor']>=0 and x['history']==history)
        if actions!=original['actions'] or row['classes']!=169:raise ValueError('legal complete169 actions required')
        hands=[]
        for h,hand in enumerate(model.CLASSES):
            p=pi[start+h*n:start+(h+1)*n];q=ev[start+h*n:start+(h+1)*n]
            if len(p)!=n or any(not math.isfinite(x) or x<0 or x>1 for x in p) or not math.isclose(math.fsum(p),1,abs_tol=1e-10):raise ValueError('normalized strategy required')
            if any(x is None or not math.isfinite(x) for x in q):raise ValueError('missing actionEV; do not0-fill')
            hands.append({'hand':hand,'frequencies':p,'action_ev_bb':q,'model_ev_bb':math.fsum(a*b for a,b in zip(p,q))})
        ranges.append({'context':context,'history':history,'position':'SB' if original['actor']==0 else 'BB','actions':[{'kind':'raise','raise_to_bb':int(a.split('_')[-1])/2} if a.startswith('raise_to_') else {'kind':a} for a in actions],'hands':hands})
    return {'schema':'pokerid-population-research-ranges-v1','status':'RESEARCH / real-game GTO precision unverified','normal_gto_eligible':False,'formal_profile':False,'condition':{'players':2,'stack_bb':50,'blinds_bb':[.5,1.],'ante_bb':0,'rake':0,'raise_to_bb':[2.5,9.,21.,50.],'format_qualification':'UNKNOWN;explicit HU chipEV research condition'},'epoch':result['epoch'],'policy_checkpoint_digest':result['state_digest'],'coverage':{'physical_flops':22100,'population_flops':22100,'contexts':4,'hands_per_context':169},'restricted_nashconv_interval_bb':result['restricted_nashconv_interval_bb'],'real_game_approximation_error':'UNKNOWN','external_GTO':'NOT PERFORMED','ranges':ranges}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=export(json.loads(a.input.read_text()));a.output.write_text(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n');print('PASS4research contexts/676rows;ordinaryGTO admission forbidden')
