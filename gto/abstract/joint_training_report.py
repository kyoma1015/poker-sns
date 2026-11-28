"""Fail-closed admission of full-epoch performance and restricted-game evidence."""
import math

def compare(legacy,vector,parity,evaluations):
    if not all(p.get('complete_epoch') and p.get('blocks')==3510 for p in (legacy,vector)):
        raise ValueError('both complete same-budget epochs required')
    if legacy['parent_logical_digest']!=vector['parent_logical_digest']:raise ValueError('different actual history')
    if parity['orbits']!=1755:raise ValueError('full population parity required')
    for p in (legacy,vector):
        if not math.isfinite(p['cpu_seconds']) or p['cpu_seconds']<=0:raise ValueError('measured finite CPU required')
    evaluated={}
    for backend in ('legacy','vector'):
        r=evaluations[backend]
        if r['coverage']!=1 or r['evaluated_orbits']!=1755 or r['epoch']!=4:raise ValueError('full independent BR required')
        nc=r['restricted_nashconv_interval_bb']
        if len(nc)!=2 or not all(math.isfinite(x) for x in nc) or nc[0]>nc[1]:raise ValueError('finite ordered bound required')
        evaluated[backend]={'nashconv_interval_bb':nc,'sb_br_gain_bb':r['sb_br_gain_bb'],'bb_br_gain_bb':r['bb_br_gain_bb']}
    return {'cpu_speedup':legacy['cpu_seconds']/vector['cpu_seconds'],'array_parity_pass':parity['max_array_difference']<1e-8,'policy_parity_pass':parity['max_policy_difference']<1e-8,'evaluations':evaluated,'normal_GTO_added':0,'formal_acceptance':[0,12],'real_game_error':'UNKNOWN','external_GTO':'NOT PERFORMED'}
