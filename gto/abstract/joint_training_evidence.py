"""Bind research rows to actual average mass; disclose zero-mass extensions."""
import math
from gto.abstract import joint_stream as s,joint_stream_export as e,fullsupport as fs

def export(result,store):
    if result['epoch']!=store.meta()['epoch'] or result['state_digest']!=store.digest():raise ValueError('result and actual policy checkpoint differ')
    prefix=s.unpack(store.get('pre'));P=store.pre
    rows=[r for r in s.layout(1)[2] if r[0]<P]
    pi=s.strategy(prefix[:P],prefix[P:2*P],rows,True)
    reported=fs.unpack(result['preflop_frequency'])
    if len(pi)!=len(reported) or any(abs(x-y)>1e-10 for x,y in zip(pi,reported)):raise ValueError('result frequency and actual average differ')
    packet=e.export(result);supported={}
    for out in packet['ranges']:
        layout=next(r for r in result['preflop_layout'] if r['history']==out['history']);n=len(layout['actions']);start=layout['base'];count=0
        for h,hand in enumerate(out['hands']):
            at=start+h*n;mass=math.fsum(prefix[P+at:P+at+n]);r=math.fsum(max(0.,v) for v in prefix[at:at+n]);count+=mass>0
            hand['average_mass']=mass;hand['positive_counterfactual_regret_mass']=r
            hand['strategy_source']='POSITIVE_AVERAGE_MASS' if mass>0 else 'ZERO_AVERAGE_MASS_UNIFORM_EXTENSION'
            hand['average_supported']=mass>0
        supported[out['context']]={'supported':count,'rows':169,'uniform_extension_rows':169-count}
    packet['coverage']['average_supported_hands']=supported
    packet['zero_mass_warning']='Normalized169 rows are not proof of learned average support. Uniform zero-mass extensions are explicit model-policy definitions,not independently verified off-path GTO recommendations.'
    return packet
