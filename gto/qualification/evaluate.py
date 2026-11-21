"""Bounded full-game counterexample probe. No solver, full BR upper, or promotion."""
import argparse,hashlib,json,math,random,shutil,time
from fractions import Fraction
from pathlib import Path
from gto.qualification.build import load
from gto.qualification.policy import ROOT,Profile,legal,act,hand,sha
from gto.abstract.model import classes,chance,CLASSES
DELTA=.001/(4*(2*169+4))
class Moments:
    def __init__(self):self.n=0;self.mean=0.;self.m2=0.
    def add(self,x):
        self.n+=1;d=x-self.mean;self.mean+=d/self.n;self.m2+=d*(x-self.mean)
    def result(self,lo,hi):
        if self.n<2:return {'n':self.n,'mean':self.mean if self.n else None,'interval':[lo,hi],'halfwidth':None}
        radius=math.sqrt(2*max(0,self.m2/(self.n-1))*math.log(2/DELTA)/self.n)+7*(hi-lo)*math.log(2/DELTA)/(3*(self.n-1))
        return {'n':self.n,'mean':self.mean,'interval':[max(lo,math.nextafter(self.mean-radius,-math.inf)),min(hi,math.nextafter(self.mean+radius,math.inf))],'halfwidth':radius}

def choose(row,u):
    z=0.
    for action,w,child in row:
        z+=w
        if u<z:return action,child
    return row[-1][0],row[-1][2]

def rollout(profile,rules,native,game,deck,tape,context,deviation=False,crosscheck=False):
    config={k:v for k,v in game._native_rules.items() if k not in ('rate_num','rate_den')};config['rake_rate']=Fraction(config['rake_rate'])
    b=rules.Betting([100,100],rules.Rules(**config));cursor=('pre',0,0);holes=[deck[:2],deck[2:4]];board=deck[4:9]
    state=native.NativeState(game) if crosscheck else None
    if state:
        for card in deck[:4]:state.apply_action(card)
    steps=0
    while not b.done:
        if state:
            while state.is_chance_node():state.apply_action(board[len(state.audit()['board'])])
            assert state.current_player()==b.actor and state.legal_actions()==legal(b)
            audit=state.audit()
            for key in ('round','price','last_full','remaining','street','live','dead','folded','history'):
                expected=getattr(b,key);expected=[list(x) for x in expected] if key=='history' else expected
                assert audit[key]==expected,(key,audit[key],expected)
        if context=='vs_open' and not b.history:
            action,child=7,('pre',profile.nodes[0]['children'][2],0)
        elif deviation and ((context=='rfi' and not b.history) or (context=='vs_open' and len(b.history)==1)):
            action,child=(8 if context=='rfi' else 22),None # raise-to3BB /10BB; normalized chips+2
        else:
            visible=board[:(0,3,4,5)[b.round]]
            row=profile.row(cursor,b,holes[b.actor],visible)
            public_key=json.dumps([b.round,b.history],separators=(',',':'))
            # Tape generated independently of cards; identical public histories share draws.
            if public_key not in tape:tape[public_key]=random_tape(tape['seed'],public_key)
            action,child=choose(row,tape[public_key])
        if state:state.apply_action(action)
        act(b,action);cursor=profile.advance(child,b);steps+=1
        if steps>64:raise AssertionError('unexpected unbounded path')
    if state:
        while state.is_chance_node():state.apply_action(board[len(state.audit()['board'])])
        assert state.is_terminal()
    ranks=[native.rank7(h+board) for h in holes]
    if crosscheck:
        reference=[rules.rank7(h+board) for h in holes]
        assert (ranks[0]>ranks[1],ranks[0]==ranks[1])==(reference[0]>reference[1],reference[0]==reference[1])
    net=b.settle(ranks,b.round>=1)['net']
    if state:assert state.returns()==net,(state.returns(),net)
    win=1. if ranks[0]>ranks[1] else .5 if ranks[0]==ranks[1] else 0.
    return [v/2 for v in net],profile.shadow(cursor,win)

def random_tape(seed,key):
    # first53 unbiased bits from independent SHA256-derived deterministic stream
    raw=hashlib.sha256((str(seed)+'|'+key).encode()).digest()
    return (int.from_bytes(raw[:8],'big')>>11)/2**53

def history_mass(profile):
    counts,prob=chance(classes());opens=[profile.pi[2*169+h] for h in range(169)]
    reach=sum(len(g)*opens[h]/1326 for h,g in enumerate(classes()))
    posterior=[sum(prob[i*169+j]*opens[i] for i in range(169))/reach for j in range(169)]
    return reach,posterior

def gate(report):
    reasons=['SPECIFICATION_NOT_APPROVED','FULL_NATIVE_BR_UPPER_BOUND_MISSING','UNIFORM_CONTINUATION_ERROR_BOUND_MISSING','OMITTED_ACTION_GAIN_UPPER_BOUND_MISSING']
    if report['gain_bb']['interval'][0]>.05:reasons.append('FEASIBLE_DEVIATION_REFUTES_PROPOSED_GAIN_LIMIT')
    if any(x['baseline']['halfwidth'] is None or x['baseline']['halfwidth']>.05 for x in report['hands'].values()):reasons.append('ALL169_EV_PRECISION_NOT_MET')
    return {'status':'BLOCKED_UNVERIFIED','ordinary_registry_admission':False,'reasons':reasons,'full_native_br_upper_bb':None,'full_native_nashconv_bb':None,'uniform_continuation_error_upper_bb':None}

def atomic(path,value):
    path=Path(path);temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');temporary.replace(path)

def run(builddir,output,samples=16384,seconds=180):
    output=Path(output)
    if output.exists():raise ValueError('fresh output required; prior evidence must not be overwritten')
    if not 2<=samples<=16384 or not 1<=seconds<=180:raise ValueError('bounded preregistered budget')
    if shutil.disk_usage(output.parent).free<2*1024**3:raise ValueError('2GiB reserve required')
    rules,native=load(builddir)
    from gto.native.training import NativeGame
    game=NativeGame([100,100]);start=time.monotonic();reports=[]
    for mi,name in enumerate(('learned_small','learned_large')):
        profile=Profile(name);reach,posterior=history_mass(profile)
        for ci,context in enumerate(('rfi','vs_open')):
            rng=random.Random(20261117+1009*mi+17*ci);hero=ci
            baseline=Moments();deviant=Moments();gain=Moments();discrepancy=Moments();hands=[[Moments(),Moments()] for _ in CLASSES];draws=0;checks=0
            for i in range(samples):
                if time.monotonic()-start>seconds:break
                while True:
                    deck=rng.sample(range(52),9);draws+=1
                    if context=='rfi' or rng.random()<profile.pi[2*169+hand(deck[:2])]:break
                tape={'seed':rng.getrandbits(128)}
                values,shadow=rollout(profile,rules,native,game,deck,tape,context,crosscheck=i<256)
                changed,_=rollout(profile,rules,native,game,deck,tape,context,deviation=True,crosscheck=i<256)
                checks+=i<256
                baseline.add(values[hero]);deviant.add(changed[hero]);gain.add(changed[hero]-values[hero]);h=hand(deck[2*hero:2*hero+2]);hands[h][0].add(values[hero]);hands[h][1].add(changed[hero])
                if shadow is not None:discrepancy.add(values[hero]-(shadow if hero==0 else -shadow))
                if (i+1)%1024==0:
                    atomic(output.with_suffix('.checkpoint.json'),{'schema':'qualification-progress-v1','automatic_resume':False,'profile_digest':profile.digest,'model':name,'context':context,'samples_completed':i+1,'rng_state':rng.getstate(),'moments':{'baseline':vars(baseline),'deviant':vars(deviant),'gain':vars(gain),'hands':[[vars(a),vars(b)] for a,b in hands]},'completed_reports':reports})
            report={'model':name,'context':context,'profile_identity':profile.identity,'totalized_policy_digest':profile.digest,'accepted_deals':baseline.n,'draws':draws,'native_python_rank_and_settlement_crosschecks_per_arm':checks,'baseline_ev_bb':baseline.result(-50,50),'deviation_ev_bb':deviant.result(-50,50),'gain_bb':gain.result(-100,100),'execution_cashflow_discrepancy_bb':discrepancy.result(-100,100),'hands':{label:{'baseline':a.result(-50,50),'deviation':b.result(-50,50)} for label,(a,b) in zip(CLASSES,hands)},'source_open_history_reach':reach if context=='vs_open' else 1.,'source_bb_class_posterior':posterior if context=='vs_open' else None}
            report['root_feasible_gain_lower_bb']=report['gain_bb']['interval'][0]*(reach if context=='vs_open' else 1.)
            report['qualification']=gate(report);reports.append(report)
            print(json.dumps({'model':name,'context':context,'n':baseline.n,'gain':report['gain_bb'],'seconds':time.monotonic()-start}),flush=True)
    receipt={'schema':'native-qualification-counterexample-v1','condition':{'players':2,'stacks_bb':[50,50],'bb_chips':2,'ante_bb':0,'rake_pct':0,'deck':52,'streets':'all','bet_sizes':'all legal integer-chip raise-to targets','formal_profile':False},'policy_scope':'explicit totalized evaluation policies; not original candidates unchanged','comparison_scope':'fixed legal deviation lower bounds, NOT full BR upper or NashConv','sampling':'uniform distinct ordered hole/board cards; vsopen rejection by source opener reach; shared public keyed random tape','family_failure_probability':.001,'per_metric_failure_probability':DELTA,'interval':'bounded empirical Bernstein; IEEE guard is not rigorous roundoff proof','source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'gto/qualification').glob('*.py'))},'protocol_sha256':sha(ROOT/'docs/qa/preflop-qualification-20261117/PROTOCOL.md'),'build':json.loads((Path(builddir)/'build.json').read_text()),'reports':reports,'elapsed_seconds':time.monotonic()-start,'hard_stop_seconds':seconds,'completed_fixed_budget':all(r['accepted_deals']==samples for r in reports),'ordinary_verified_rfi_vsopen_strategies':0,'formal_acceptance_complete':0,'frozen_same_game_nashconv_new':None}
    atomic(output,receipt)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--samples',type=int,default=16384);p.add_argument('--seconds',type=int,default=180);a=p.parse_args();run(a.build_dir,a.output,a.samples,a.seconds)
