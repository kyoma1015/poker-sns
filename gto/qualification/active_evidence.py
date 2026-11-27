"""Same-digest frequency/conditional EV export and independent-instance replay."""
import hashlib,json,gc
from pathlib import Path
import numpy as np
from gto.qualification import active_study
from gto.qualification.active_resume import restore
from gto.qualification.evaluate import atomic
from gto.qualification.policy import CLASSES,sha

def run(seed,mode):
    folder=active_study.ROOT/str(seed)/mode;q,identity=restore(folder,'/tmp/active-export-'+str(seed)+'-'+mode)
    initial=np.load(folder/'initial.npz');pi=q.policy();contexts={};owner_ev={}
    for owner in (0,1):
        q.evaluate_owner(pi,owner);owner_ev[owner]=(q.num.copy(),q.evden.copy())
    for name,prefix in [('RFI',[]),('vs_open_3BB',[[0,0,6]]),('vs_3bet_10BB',[[0,0,6],[0,1,20]])]:
        matches=[k for k,n in enumerate(q.nodes) if n['actor']>=0 and n['round']==0 and n['native_prefix']==prefix]
        if len(matches)!=1:raise ValueError('required preflop context '+name)
        k=matches[0];n=q.nodes[k];count=len(n['children']);num,den=owner_ev[n['actor']];rows=[]
        lookup={key[0]:j for j,key in enumerate(q.keys[k])}
        for h,label in enumerate(CLASSES):
            j=lookup.get(h)
            if j is None:rows.append(dict(hand=label,unreachable_in_board_law=True));continue
            at=q.base[k]+j*count;evat=q.prebase[k]+h*count
            rows.append(dict(hand=label,frequencies=pi[at:at+count].tolist(),conditional_EV_finite_board_bb=np.divide(num[evat:evat+count],den[evat:evat+count],out=np.zeros(count),where=den[evat:evat+count]>0).tolist(),positive_CF_mass=bool(np.all(den[evat:evat+count]>0))))
        contexts[name]=dict(native_actions=n['native_actions'],hands=rows)
    atomic(folder/'preflop.json',dict(checkpoint_sha256=identity['checkpoint_sha256'],contexts=contexts,EV_scope='exact finite board/action law; no full-native precision certificate',full_native_EV_precision_pass_cells=0))
    q.step();expected=(q.R.copy(),q.A.copy(),q.visits.copy());q.save(folder/'nextstep-proof.npz');del q;gc.collect()
    other,_=restore(folder,'/tmp/active-export-'+str(seed)+'-'+mode);other.step()
    for got,wanted in zip((other.R,other.A,other.visits),expected):np.testing.assert_array_equal(got,wanted)
    atomic(folder/'replay.json',dict(independent_instance_nextstep_exact=True,t=other.t,nextstep_sha256=sha(folder/'nextstep-proof.npz'),source_sha256=sha(Path(__file__)),warm_prior_source_sha256=identity['initial_sha256'],R_A_visits_SHA256=[hashlib.sha256(x.tobytes()).hexdigest() for x in expected],RNG='none: all fixed-board chance/private outcomes integrated',proof_checkpoint_not_selected=True))
if __name__=='__main__':
    for seed in (17120101,17120102):
        for mode in ('refine','bounded'):run(seed,mode)
