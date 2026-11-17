"""Read-only native root profile vs legal SB-fold deviation; NOT complete BR.

No Python betting or surrogate continuation. Native public observations only.
Fixed8192worlds/policy, <=30s/policy, no confidence claim on an incomplete run.
"""
import gzip,json,math,random,time
from pathlib import Path
from gto.qualification.build import load
from gto.qualification.native_mccfr import choose
from gto.qualification.public_response import Observation
from gto.qualification.variance_mccfr import VarianceSolver
from gto.qualification.external_first import ExternalFirst
from gto.native.training import NativeGame


def probe(build,folder):
    folder=Path(folder);_,native=load(build);game=NativeGame([100,100]);reports=[]
    for name in ('raw-zero','orbit-cv','orbit-external'):
        path=folder/(name+'-checkpoint.json.gz');d=json.loads(gzip.decompress(path.read_bytes()))
        if name=='orbit-external':s=ExternalFirst(None,native)
        else:s=VarianceSolver(None,native,suits=d['identity']['key']=='exact-suit-orbit',control=d['identity']['baseline']=='exact-fold')
        s.restore(d);before=s.policy_digest;master=random.Random(17113000);values=[];start=time.monotonic()
        for _ in range(8192):
            if time.monotonic()-start>30:break
            deck=master.sample(range(52),9);rng=random.Random(master.getrandbits(128))
            state=native.NativeState(game)
            for card in deck[:4]:state.apply_action(card)
            while not state.is_terminal():
                if state.is_chance_node():
                    state.apply_action(deck[4+len(state.audit()['board'])]);continue
                a=state.audit();actor=state.current_player()
                o=Observation(actor,tuple(sorted(a['holes'][actor])),tuple(a['board']),
                    a['round'],a['price'],a['last_full'],tuple(a['remaining']),tuple(a['street']),
                    tuple(a['live']),tuple(a['dead']),tuple(a['folded']),tuple(tuple(h) for h in a['history']),
                    tuple(state.legal_actions()))
                action=choose(o.actions,s.row(o,True),rng);state.apply_action(action)
            net=[v/2 for v in state.returns()]
            assert sum(net)==0 and all(-50<=v<=50 for v in net)
            values.append(net[0])
        assert before==s.policy_digest
        n=len(values);mean=sum(values)/n
        # Three simultaneous two-sided profile means, family failure<=.001.
        radius=100*math.sqrt(math.log(2*3/.001)/(2*n)) if n==8192 else None
        report=dict(name=name,policy_digest=before,n=n,elapsed_seconds=time.monotonic()-start,
                    profile_sb_ev_bb=mean,profile_interval_bb=[max(-50,mean-radius),min(50,mean+radius)] if radius else None,
                    fixed_legal_deviation='SB fold at root for every own hand; rest irrelevant',deviation_ev_bb=-.5,
                    feasible_deviation_gain_bb=-.5-mean,
                    feasible_deviation_gain_interval_bb=[-.5-mean-radius,-.5-mean+radius] if radius else None,
                    full_br_gain_lower_bb=max(0,-.5-mean-radius) if radius else None,
                    full_zero_sum_nashconv_lower_bb=max(0,-.5-mean-radius) if radius else None,
                    full_br_gain_upper_bb=None,nashconv_bb=None,nashconv_upper_bb=None,
                    completed=n==8192,confidence_family=.999,method='fixed-n Hoeffding; native payoff range [-50,50]',
                    scope='root profile EV and feasible deviation lower bounds only; not optimized BR/upper',
                    ordinary_registry_admission=False)
        reports.append(report)
        (folder/'native-fold-probe.json').write_text(json.dumps(reports,indent=2)+'\n')
        print(report,flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--folder',required=True);a=p.parse_args();probe(a.build,a.folder)
