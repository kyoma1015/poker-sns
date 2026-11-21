"""Read-only attribution labels from cached exact data; no native reevaluation."""
import hashlib,heapq,json,sqlite3,zlib
from pathlib import Path
from gto.abstract import pure_br as p,joint_stream as s,joint_stream_cache as cache,joint_realization as mix,model

def enrich(root,temporary,source=None):
    root=Path(root);temporary=Path(temporary);result=json.loads((root/'result.json').read_text())
    if not result['complete'] or not result['pass_tolerance']:raise ValueError('complete independently realized BR required')
    db=sqlite3.connect((root/'policy.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    def get(key):return zlib.decompress(db.execute('select value from state where key=?',(key,)).fetchone()[0])
    rows=cache.population();indices={tuple(r['representative']):i for i,r in enumerate(rows)};mass=sum(r['multiplicity'] for r in rows);ns=s.tree()[0];pre=model.tree();prefix=get('prefix');lookups={};histories={}
    def walk(k,history):
        if k in histories and histories[k]!=history:raise ValueError('public history ambiguity')
        histories[k]=history
        for a,c in enumerate(pre[k].get('children',[])):walk(c,history+[pre[k]['actions'][a]])
    walk(0,[])
    # Preflop entries already integrate all boards, so a global top50 can hide
    # every individual flop info. Rank flop infos separately from cached exact
    # advantages, without running another payoff/BR kernel or selecting a policy.
    heap=[];serial=0
    for i,row in enumerate(rows):
        obj,_=cache.read('/workspace/joint-stream-cache',row);T=len(obj['codes']);layout=s.layout(T);post=get('b:'+str(i));pure=p.pure_policy(prefix,post,T);reach=mix.info_reach(pure,obj['codes']);raw=(temporary/(str(i)+'.bin')).read_bytes()
        if hashlib.sha256(raw).digest()!=get('d:'+str(i)):raise ValueError('diagnostic cache mismatch')
        diag=s.unpack(zlib.decompress(raw));which=0;weight=row['multiplicity']/mass
        for start,types,n,k in layout[2]:
            if start>=layout[3]:
                for typ in range(types):
                    a=post[which];g,d=diag[2*which:2*which+2];which+=1;own=reach[start+typ*n+a];gain=weight*own*g
                    if gain and (len(heap)<40 or abs(gain)>heap[0][0]):
                        entry={'owner':ns[k]['actor'],'node':k,'hand':model.CLASSES[obj['codes'][typ]//8],'action_index':a,'gain_bb':gain,'reach':weight*own*d,'flop':row['representative']}
                        serial+=1;item=(abs(gain),serial,entry)
                        if len(heap)<40:heapq.heappush(heap,item)
                        else:heapq.heapreplace(heap,item)
    result['top_post_information_sets']=[e for _,_,e in sorted(heap,reverse=True)]
    entries=result['top_information_sets']+result['negative_information_sets']+result['top_post_information_sets'];baseline_pre=None;total=s.unpack(get('sum'));P=s.layout(1)[3];L=2*len(pre)*169
    if source is not None:
        obj,_=cache.read('/workspace/joint-stream-cache',rows[0]);reg,avg=source.state(0,len(obj['codes']));policy=s.strategy(reg,avg,s.layout(len(obj['codes']))[2],True);baseline_pre=(policy,mix.info_reach(policy,obj['codes']))
    for flop in {tuple(x['flop']) for x in entries if x['flop'] is not None}:
        i=indices[flop];row=rows[i];obj,_=cache.read('/workspace/joint-stream-cache',row);T=len(obj['codes']);layout=s.layout(T);post=get('b:'+str(i));pure=p.pure_policy(prefix,post,T);reach=mix.info_reach(pure,obj['codes']);raw=(temporary/(str(i)+'.bin')).read_bytes()
        if hashlib.sha256(raw).digest()!=get('d:'+str(i)):raise ValueError('diagnostic cache mismatch')
        diag=s.unpack(zlib.decompress(raw));which=0;lookup={};weight=row['multiplicity']/mass;base_reach=None
        if source is not None:
            reg,avg=source.state(i,T);base_policy=s.strategy(reg,avg,s.layout(T)[2],True);base_reach=mix.info_reach(base_policy,obj['codes'])
        for start,types,n,k in layout[2]:
            if start>=layout[3]:
                for typ in range(types):
                    a=post[which];g,d=diag[2*which:2*which+2];which+=1;at=start+typ*n+a;own=reach[at];code=obj['codes'][typ];key=(k,model.CLASSES[code//8],a,weight*own*g,weight*own*d)
                    lookup.setdefault(key,[]).append({'signal':code,'baseline_root_reach':None if base_reach is None else weight*base_reach[at]*d,'single_info_deviation_gain_bb':None if base_reach is None else weight*base_reach[at]*g})
        lookups[flop]=lookup
    for entry in entries:
        node=ns[entry['node']];entry['seat']='SB' if entry['owner']==0 else 'BB'
        if entry['flop'] is not None:
            key=(entry['node'],entry['hand'],entry['action_index'],entry['gain_bb'],entry['reach']);codes=lookups[tuple(entry['flop'])].get(key)
            if not codes:raise ValueError('no exact cached private-info attribution match')
            entry['own_private_signal_candidates']=codes;entry['unique_signal_identified']=len(codes)==1
            entry['preflop_history']=histories[node['preflop_leaf']];entry['flop_history']=node['history'];pot=pre[node['preflop_leaf']]['value'];entry['initial_flop_pot_bb']=pot;entry['initial_flop_spr']=(50-pot/2)/pot
        else:entry['preflop_history']=node['history'];entry['own_preflop_class']=entry['hand']
        entry['legal_action']=node['actions'][entry['action_index']]
        entry['preflop_history_amount_unit']='chips;2chips=1BB'
    for entry in result['top_drivers']+result['top_negative_drivers']:
        node=ns[entry['node']];entry['seat']='SB' if entry['owner']==0 else 'BB';entry['preflop_history']=histories[node['preflop_leaf']] if node['street']=='flop' else node['history']
        if node['street']=='preflop' and baseline_pre is not None:
            layout=s.layout(1);start,_,n,_=next(r for r in layout[2] if r[3]==entry['node']);a=node['actions'].index(entry['action']);at=start+model.CLASSES.index(entry['hand'])*n+a;own=baseline_pre[1][at]
            entry['baseline_root_reach']=own*total[2*L+P+at];entry['single_info_deviation_gain_bb']=own*total[2*L+at]
    stats=json.loads(get('verify'));groups={}
    for key,(gain,reach) in stats['bins'].items():
        owner,k,hand,a=map(int,key.split('/'));node=ns[k];label=(owner,node['street'],tuple(histories[node['preflop_leaf']] if node['street']=='flop' else node['history']));v=groups.setdefault(label,[0.,0.,0.]);v[0]+=gain;v[1]+=max(0,gain);v[2]+=min(0,gain)
    result['signed_phase_contributions']=[{'owner':o,'street':street,'preflop_history':list(hist),'net_gain_bb':v[0],'positive_bb':v[1],'negative_bb':v[2]} for (o,street,hist),v in sorted(groups.items(),key=lambda item:abs(item[1][0]),reverse=True)]
    result['diagnostic_scope']='Target-profile root improvement,all signed terms;equal-gain private-feature aliases listed explicitly. Root BR attribution uses BR ownreach;single-info changes use BASELINE ownreach and differ. Off-path completion can shift attribution between earlier/later nodes without changing rootNC. Not fullNLHE or a new equilibrium.'
    db.close();return result
