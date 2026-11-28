"""Bounded native legal-size study of one sparse joint external-sampling engine."""
import argparse,copy,gc,gzip,json,math,random,resource,time,tempfile,shutil
from pathlib import Path
import numpy as np
from gto.abstract import model
from gto.qualification import sparse_solver as s,fullstreet_solver as old
from gto.qualification.action_native import native_value as raw_value,interval
from gto.qualification.coupled_evaluate import Extra
from gto.qualification.range_study import GeneralNuts
from gto.qualification.native_mccfr import choose,betting
from gto.qualification.policy import act,sha
from gto.qualification.public_response import Observation,observe
from gto.qualification.preflop_release_solver import load_policy
from gto.qualification.evaluate import atomic
from gto.native.training import NativeGame


def rb_value(policy,native,game,deck,tape,module):
    state=native.NativeState(game);rng=random.Random(tape>>64)
    for c in deck[:4]:state.apply_action(c)
    while not state.is_terminal():
        a=state.audit()
        if state.is_chance_node():
            if a['remaining']==[0,0] and len(a['board'])<5:
                if a['live']!=[100,100]:raise ValueError('HU50 allin stake')
                eq=module.equity_prefix(a['holes'][0]+a['holes'][1],a['board'],16,tape&((1<<64)-1))
                return 50*(2*eq-1)
            state.apply_action(deck[4+len(a['board'])]);continue
        p=state.current_player();o=Observation(p,tuple(sorted(a['holes'][p])),tuple(a['board']),a['round'],a['price'],a['last_full'],tuple(a['remaining']),tuple(a['street']),tuple(a['live']),tuple(a['dead']),tuple(a['folded']),tuple(tuple(h) for h in a['history']),tuple(state.legal_actions()))
        state.apply_action(choose(o.actions,policy.row(o,True),rng))
    return state.returns()[0]/2


def samples(seed,n):
    r=random.Random(seed);return [(r.sample(range(52),9),r.getrandbits(128)) for _ in range(n)]

def selection(q,native,module,worlds):
    probe=Extra(q,'open3p5');base=[];gain=[]
    for deck,tape in worlds:
        v=rb_value(q,native,NativeGame([100,100]),deck,tape,module);base.append(v);gain.append(rb_value(probe,native,NativeGame([100,100]),deck,tape,module)-v)
    return dict(SB_EV_bb=float(np.mean(base)),open3p5_gain_bb=float(np.mean(gain)),n=len(worlds))

def archive_save(q,folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='sparse-save-') as stage:
        q.save(stage);src=Path(stage)/'checkpoint.bin'
        with src.open('rb') as inp,(folder/'checkpoint.bin.gz').open('wb') as out,gzip.GzipFile(fileobj=out,mode='wb',mtime=0) as z:
            shutil.copyfileobj(inp,z)
        shutil.copyfile(Path(stage)/'checkpoint.json',folder/'checkpoint.json')

def archive_restore(q,folder):
    folder=Path(folder)
    with tempfile.TemporaryDirectory(prefix='sparse-restore-') as stage:
        raw=Path(stage)/'checkpoint.bin'
        with gzip.open(folder/'checkpoint.bin.gz','rb') as inp,raw.open('wb') as out:shutil.copyfileobj(inp,out)
        shutil.copyfile(folder/'checkpoint.json',Path(stage)/'checkpoint.json');q.restore(stage)


def train(module,native_build,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);base=load_policy(native_build,old.old.ARTIFACT);resource_records=[];results=[]
    for seed in (17120101,17120102):
        w,origin=s.warm(module,seed);folder=out/str(seed);folder.mkdir(exist_ok=True)
        if seed==17120101 and not (out.parent/'hu'/'resource-comparison.json').exists():
            for full,fine in ((True,True),(False,False),(False,True)):
                q=s.Solver(module,w,origin,seed+1000000,full=full,refined=fine);start=time.monotonic();last=None
                for _ in range(4):
                    last=q.step(1.)
                    if not last['complete']:break
                resource_records.append(dict(full=full,refined=fine,last=last,stats=q.core.stats(),seconds=time.monotonic()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024));del q;gc.collect()
            atomic(out/'resource-comparison.json',dict(records=resource_records,selection='allnative rejected if incomplete; same geometry engine with strength key continues; omission errors UNKNOWN'))
        q=s.Solver(module,w,origin,seed+1100000,full=False,refined=True);del w;gc.collect();worlds=samples(seed+1400000,256)
        archive_save(q,folder/'initial');initial=selection(q,base.native,module,worlds);archive_save(q,folder/'best');best=initial['open3p5_gain_bb'];curve=[dict(iterations=0,selection=initial)];start=time.monotonic();reason='STAGE_LIMIT';training_seconds=0.
        for target in (64,256,1024):
            while q.iteration<target and time.monotonic()-start<60:
                r=q.step(min(1.,max(.01,60-(time.monotonic()-start))))
                if not r['complete']:reason=r['error'];break
            if not r['complete'] or q.iteration<target:
                archive_save(q,folder/'last');break
            archive_save(q,folder/'last');v=selection(q,base.native,module,worlds);curve.append(dict(iterations=q.iteration,selection=v,stats=q.core.stats(),seconds=time.monotonic()-start));print(json.dumps(dict(seed=seed,**curve[-1])),flush=True);atomic(folder/'selection.json',dict(curve=curve))
            if v['open3p5_gain_bb']>best+1e-10:reason='FIRST_SELECTION_WORSENING';break
            best=v['open3p5_gain_bb'];archive_save(q,folder/'best')
        archive_restore(q,folder/'best');atomic(folder/'freeze.json',dict(policy_digest=q.policy_digest,iterations=q.iteration,source_sha256=sha(Path(__file__)),selection_finished=True,stop_reason=reason,final_evaluations=0))
        result=dict(seed=seed,curve=curve,reason=reason,best_iterations=q.iteration,stats=q.core.stats(),seconds=time.monotonic()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,ordinary_registry_admission=False)
        atomic(folder/'training.json',result);results.append(result);del q;gc.collect()
    return results


class Force:
    def __init__(self,base,action):self.base,self.action=base,action
    def row(self,o,average=False):
        if not o.history:
            if self.action not in o.actions:raise ValueError('forced native root action')
            return [float(a==self.action) for a in o.actions]
        return self.base.row(o,True)

def profile_stats(q):return copy.deepcopy(q.stats)

def evaluate(module,native_build,out):
    from gto.qualification.variance_study import compressed
    out=Path(out);base=load_policy(native_build,old.old.ARTIFACT);native=base.native;game=NativeGame([100,100]);final_worlds=samples(17126301,8192);discovery_worlds=samples(17126201,256);records=[]
    for si,seed in enumerate((17120101,17120102)):
        folder=out/str(seed);w,origin=s.warm(module,seed);q=s.Solver(module,w,origin,seed+1100000);q.native=native;del w;gc.collect();archive_restore(q,folder/'best');frozen=q.policy_digest
        parent=old.read_policy(s.PARENT/str(seed),old.load('/tmp/fullstreet-build/fullstreet.so'),base,'policy-best');parent.average_mass=parent.average_mass>0
        kinds=['open3p5','threebet10p5','river_jam','river_nuts'];probes=[Extra(q,k) if k!='river_nuts' else GeneralNuts(q) for k in kinds];monitor=Coverage(q);profiles=[parent,Extra(parent,'open3p5'),monitor,*probes];values=[[] for _ in profiles];raw=[];start=time.monotonic()
        identity=dict(seed=17126301,n=8192,worlds=final_worlds,policy_digest=frozen,parent_digest=parent.policy_digest,source_sha256=sha(Path(__file__)),native_binary_sha256=sha(Path(native.__file__)),confidence_family=.999,events=40,allocated_delta=.0003,overall_three_family_delta=.001,estimator='same native policy; exact flop990/turn44 all-in suffix; uniform16preflop conditionalrunouts; CRN',formal_profile=False)
        cache=folder/'native.json'
        if cache.exists() and json.loads(cache.read_text()).get('status')=='COMPLETE_UNVERIFIED':
            native_result=json.loads(cache.read_text());assert native_result['identity']['policy_digest']==frozen and native_result['identity']['seed']==17126301
            saved=json.loads(gzip.decompress((folder/'native-progress.json.gz').read_bytes()));assert saved['completed']==8192;values=saved['values'];raw=saved['raw'];delta=.0003/40
        else:
            for i,(deck,tape) in enumerate(final_worlds):
                if time.monotonic()-start>90:atomic(folder/'native.json',dict(status='INCOMPLETE_TIME_LIMIT',completed=i));break
                monitor.begin_world()
                for p,v in zip(profiles,values):v.append(rb_value(p,native,game,deck,tape,module))
                monitor.end_world()
                if i<1024:raw.append(raw_value(q,native,game,deck,tape>>64))
                if (i+1)%1024==0:compressed(folder/'native-progress.json.gz',dict(identity=identity,completed=i+1,values=values,raw=raw));print(json.dumps(dict(seed=seed,worlds=i+1,seconds=time.monotonic()-start)),flush=True)
            if len(values[0])!=8192:return
            assert frozen==q.policy_digest
            delta=.0003/40;gainold=[a-b for a,b in zip(values[1],values[0])];gainnew=[a-b for a,b in zip(values[3],values[2])];native_result=dict(status='COMPLETE_UNVERIFIED',identity=identity,old_EV_bb=interval(values[0],-50,50,delta),new_EV_bb=interval(values[2],-50,50,delta),paired_EV_change_bb=interval([a-b for a,b in zip(values[2],values[0])],-100,100,delta),old_open3p5_gain_bb=interval(gainold,-100,100,delta),new_open3p5_gain_bb=interval(gainnew,-100,100,delta),open3p5_gain_reduction_bb=interval([a-b for a,b in zip(gainold,gainnew)],-200,200,delta),deviations={k:interval([(1 if k=='open3p5' else -1)*(a-b) for a,b in zip(v,values[2])],-100,100,delta) for k,v in zip(kinds,values[3:])},variance=dict(n=1024,raw_sample_variance=float(np.var(raw,ddof=1)),conditional_sample_variance=float(np.var(values[2][:1024],ddof=1)),raw_minus_conditional_bb=interval([a-b for a,b in zip(raw,values[2][:1024])],-100,100,delta)),new_query_stats=monitor.counts,new_coverage=monitor.world_counts,seconds=time.monotonic()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,full_native_BR_upper=None,full_native_NashConv=None,all169_action_precision=None,omitted_action_error_upper=None,continuation_error_upper=None,ordinary_registry_admission=False)
            atomic(folder/'native.json',native_result)
        records.append(native_result)
        # All legal root actions on disjoint discovery set. No selected-action PASS.
        scan_cache=folder/'all-root-discovery.json'
        if scan_cache.exists():
            scan_record=json.loads(scan_cache.read_text());assert scan_record['seed']==17126201 and scan_record['completed']==scan_record['total_legal'];other=scan_record['selected_other']
        else:
            q.stats={r:dict(queries=0,untrained=0,warm=0) for r in range(4)};actions=base.native.NativeState(game)
            for c in discovery_worlds[0][0][:4]:actions.apply_action(c)
            legal_actions=list(actions.legal_actions());scan=[];startscan=time.monotonic();basevals=[rb_value(q,native,game,d,t,module) for d,t in discovery_worlds]
            for a in legal_actions:
                if time.monotonic()-startscan>90:break
                vals=[rb_value(Force(q,a),native,game,d,t,module)-v for (d,t),v in zip(discovery_worlds,basevals)]
                scan.append(dict(native_action=a,raise_to_BB=(a-2)/2 if a>1 else None,gain_bb=interval(vals,-100,100,.001/(len(legal_actions)*2))))
            other=max((r for r in scan if r['native_action'] not in (0,1,9)),key=lambda r:r['gain_bb']['mean']);atomic(folder/'all-root-discovery.json',dict(seed=17126201,n=256,total_legal=len(legal_actions),completed=len(scan),rows=scan,selected_other=other,omitted_size_upper=None,seconds=time.monotonic()-startscan,scope='fixed root actions only; all deeper histories/errors not bounded'))
        # Independent confirmation of known3.5 and selectedother. Frozen policy.
        confirm_cache=folder/'confirmation.json.gz'
        if confirm_cache.exists():
            saved=json.loads(gzip.decompress(confirm_cache.read_bytes()));assert saved['policy_digest']==frozen and saved['n']==32768
        else:
            confirm=samples(17126501,32768);attacks=[Extra(q,'open3p5'),Force(q,other['native_action'])];hist=[[],[],[],[]];oldhist=[];startconfirm=time.monotonic()
            for i,(deck,tape) in enumerate(confirm):
                if time.monotonic()-startconfirm>90:break
                v=rb_value(q,native,game,deck,tape,module);pv=rb_value(parent,native,game,deck,tape,module);po=rb_value(Extra(parent,'open3p5'),native,game,deck,tape,module);aa=[rb_value(p,native,game,deck,tape,module) for p in attacks]
                hist[0].append(aa[0]-v);hist[1].append(aa[1]-v);hist[2].append(po-pv);hist[3].append((po-pv)-(aa[0]-v))
            if len(hist[0])==32768:
                from collections import Counter
                compressed(folder/'confirmation.json.gz',dict(seed=17126501,n=32768,policy_digest=frozen,old_digest=parent.policy_digest,other_action=other['native_action'],confidence_family=.999,events=8,known_gain_bb=interval(hist[0],-100,100,.0003/8),other_gain_bb=interval(hist[1],-100,100,.0003/8),old_known_gain_bb=interval(hist[2],-100,100,.0003/8),known_reduction_bb=interval(hist[3],-200,200,.0003/8),histograms=[dict(Counter(map(str,h))) for h in hist],seconds=time.monotonic()-startconfirm,full_native_BR_upper=None,ordinary_registry_admission=False))
            else:atomic(folder/'confirmation-incomplete.json',dict(completed=len(hist[0]),target=32768,no_fixed_n_bound=True))
        # Frequencies on real native prefixes, including off-grid responses.
        freq={}
        for name,prefix in [('rfi',[]),('vs_open3',[8]),('vs_open3p5',[9]),('vs_3bet10',[8,22]),('vs_3bet10p5',[8,23])]:
            b=betting(base.rules)
            for a in prefix:act(b,a)
            freq[name]={label:dict(native_actions=observe(b,g[0],[]).actions,frequencies=q.row(observe(b,g[0],[]),True),native_action_EV_interval=None) for label,g in zip(model.CLASSES,model.classes())}
        compressed(folder/'169-frequencies.json.gz',dict(policy_digest=frozen,rows=freq,all169_action_precision=None,ordinary_registry_admission=False))
        # Freeze identity before changing to initial-prior control.
        archive_restore(q,folder/'initial');init=[rb_value(q,native,game,d,t,module) for d,t in final_worlds];atomic(folder/'initial-prior-control.json',dict(policy_digest=q.policy_digest,SB_EV_bb=interval(init,-50,50,delta),learned_minus_initial_bb=interval([a-b for a,b in zip(values[2],init)],-100,100,delta),scope='same final worlds, postselection comparison only'))
        archive_restore(q,folder/'best');del parent;gc.collect();jam_certificate(q,base.rules,module,folder,seed)
        atomic(out/'native-summary.json',dict(records=records,formal_acceptance=0,verified_RFI=0,verified_3bet=0));del q;gc.collect()
    return records

class Coverage:
    def __init__(self,base):
        self.base=base;self.counts={r:dict(queries=0,trained=0,warm_only=0,default=0) for r in range(4)};self.world_counts=dict(current_untrained=0,no_parent_or_current=0);self.flags=[False,False]
    def begin_world(self):self.flags=[False,False]
    def end_world(self):
        self.world_counts['current_untrained']+=self.flags[0];self.world_counts['no_parent_or_current']+=self.flags[1]
    def row(self,o,average=False):
        r=self.base.core.query(o.own,o.board,o.actor,o.round,o.history,o.actions,o.live,o.street,o.remaining,o.price,True);c=self.counts[o.round];c['queries']+=1
        if r['trained']:c['trained']+=1
        elif r['warm']:c['warm_only']+=1
        else:c['default']+=1
        self.flags[0]|=not r['trained'];self.flags[1]|=not r['trained'] and not r['warm'];return r['probabilities']

def jam_certificate(q,rules,module,folder,seed):
    # Exact private-opponent enumeration, no dependence on a guessed range.
    b=betting(rules);act(b,102);call=[]
    for group in model.classes():
        o=observe(b,group[0],[]);p=q.row(o,True);assert set(o.actions)=={0,1};call.append(p[o.actions.index(1)])
        assert p==q.row(observe(b,group[-1],[]),True) # preflop suit-orbit invariance
    classes={tuple(sorted(pair)):c for c,g in enumerate(model.classes()) for pair in g};rng=random.Random(17126401+seed);rows={};start=time.monotonic();K=32;delta=.0004/(169*2)
    for label,group in zip(model.CLASSES,model.classes()):
        if time.monotonic()-start>90:break
        own=list(group[0]);available=[c for c in range(52) if c not in own];mean=weight2=0.;count=0
        import itertools
        for other in itertools.combinations(available,2):
            p=call[classes[other]];eq=module.equity_prefix(own+list(other),[],K,rng.getrandbits(64));mean+=(1-p)+p*50*(2*eq-1);weight2+=p*p;count+=1
        assert count==1225;mean/=1225;radius=100*math.sqrt(math.log(2/delta)*weight2/(2*1225**2*K))
        rows[label]=dict(fold=dict(native_action=0,mean=-.5,interval=[-.5,-.5],exact=True),jam=dict(native_action=102,mean=mean,interval=[max(-50,mean-radius),min(50,mean+radius)],radius=radius,opponent_pairs=1225,boards_per_pair=K))
    atomic(folder/'169-fold-jam-EV.json',dict(policy_digest=q.policy_digest,source_sha256=sha(Path(__file__)),rng_seed=17126401+seed,bb_call_probabilities=call,rows=rows,completed_classes=len(rows),other_native_action_EV=None,full169_action_precision=None,confidence_family=.999,allocated_delta=.0004,method='exact opponentprivate enumeration and mixed fold/call integration; independent uniform conditionalboards; weighted Hoeffding perhero suit-orbit',max_jam_width=max((v['jam']['interval'][1]-v['jam']['interval'][0] for v in rows.values()),default=None),seconds=time.monotonic()-start,ordinary_registry_admission=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--library',required=True);p.add_argument('--native-build',required=True);p.add_argument('--out',required=True);p.add_argument('--evaluate',action='store_true');a=p.parse_args();(evaluate if a.evaluate else train)(s.load(a.library),a.native_build,a.out)


def generalization_pilot(module,native_build,out):
    """Two-seed fixed-budget key ablation, with independent historical discovery."""
    from gto.qualification.build import load
    rules,native=load(native_build);out=Path(out);out.mkdir(parents=True,exist_ok=True);records=[]
    for seed in (17120101,17120102):
        w,origin=s.warm(module,seed);source=Path('docs/qa/legal-size-20261124/hu-final')/str(seed);(out/str(seed)).mkdir(parents=True,exist_ok=True)
        probe=s.Solver(module,w,origin,seed+1500000);b=betting(rules);o=observe(b,[48,49],[]);r=probe.core.query(o.own,o.board,o.actor,o.round,o.history,o.actions,o.live,o.street,o.remaining,o.price,True);base_actions=r['actions'];del probe
        discovery=json.loads((source/'all-root-discovery.json').read_text());ranked=sorted([r for r in discovery['rows'] if r['native_action']>1 and r['native_action'] not in base_actions],key=lambda r:(-r['gain_bb']['mean'],r['native_action']))
        extra=[dict(round=0,history=[],actions=[r['native_action'] for r in ranked[:2]])];atomic(out/str(seed)/'support-selection.json',dict(source=str(source/'all-root-discovery.json'),source_sha256=sha(source/'all-root-discovery.json'),scope='old independent discovery now selection only; top2 omitted root means, no fixed-size special case',selected=ranked[:2],extra_support=extra))
        worlds=samples(seed+1800000,512)
        for sharing in (False,True):
            folder=out/str(seed)/('compact' if sharing else 'detailed');folder.mkdir(parents=True,exist_ok=True);q=s.Solver(module,w,origin,seed+1500000,sharing=sharing,extra_support=extra,rows=250000);q.native=native;imported=s.bootstrap_preflop(q,source/'best',rules);curve=[];start=time.monotonic();pure=0.;best=math.inf;previous=None;reason='STAGE_LIMIT'
            for target in (0,64,128):
                while q.iteration<target and pure<10:
                    at=time.monotonic();step=q.step(min(1.,10-pure));pure+=time.monotonic()-at
                    if not step['complete']:reason=step['error'];break
                if q.iteration<target:
                    if reason=='STAGE_LIMIT':reason='INCOMPLETE_BUDGET'
                    atomic(folder/'incomplete-update.json',step);break
                monitor=Coverage(q);values=[];attack=[]
                for deck,tape in worlds:
                    monitor.begin_world();v=rb_value(monitor,native,NativeGame([100,100]),deck,tape,module);monitor.end_world();values.append(v);attack.append(rb_value(Extra(q,'open3p5'),native,NativeGame([100,100]),deck,tape,module)-v)
                score=float(np.mean(attack));row=dict(iterations=q.iteration,selection_EV_bb=float(np.mean(values)),selection_open3p5_gain_bb=score,coverage=monitor.counts,path_coverage=monitor.world_counts,stats=q.core.stats(),pure_training_seconds=pure,elapsed_seconds=time.monotonic()-start);curve.append(row);atomic(folder/'selection.json',dict(curve=curve,source_sha256=sha(Path(__file__))));print(json.dumps(dict(seed=seed,sharing=sharing,**row)),flush=True)
                if previous is not None:
                    worsening=interval([a-b for a,b in zip(attack,previous)],-200,200,.01)
                    if worsening['interval'][0]>0:reason='SIGNIFICANT_SELECTION_WORSENING';break
                previous=attack
                # t0 is a control, never an eligible learned-coverage candidate.
                if target and score<best:best=score;archive_save(q,folder/'best')
            archive_restore(q,folder/'best');result=dict(seed=seed,sharing=sharing,extra_support=extra,bootstrap=imported,curve=curve,selected_iterations=q.iteration,policy_digest=q.policy_digest,stop_reason=reason,pure_training_seconds=pure,elapsed_seconds=time.monotonic()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,formal_pass=False);atomic(folder/'pilot.json',result);records.append(result);del q;gc.collect()
        del w;gc.collect()
    atomic(out/'pilot-summary.json',dict(records=records,scope='selection only, not independent final or GTO PASS'))
    return records


def finite_sharing_oracle(module,native_build,out):
    """Finite native full-action counterexample and full-information lawful BR."""
    from gto.qualification.build import load
    from gto.qualification.multiplayer_joint import Joint,observation,clone_native,path_oracle,path_br
    rules,native=load(native_build);game=NativeGame([6,6]);decks=[]
    for own in ([44,37],[40,33]):
        for other in ([41,36],[45,32]):
            for board in ([4,5,16,31,50],[6,7,20,30,49]):
                shown=list(own)+list(other)+list(board);assert len(set(shown))==9;decks.append(shown+[c for c in range(52) if c not in shown])
    classes=[-1]*2704
    for c,g in enumerate(model.classes()):
        for a,b in g:classes[52*a+b]=classes[52*b+a]=c
    data=dict(classes=classes,pi=np.array([]),support=np.array([],dtype=np.uint8),nodes=[],equity=[.5]*169,sharing=True)
    core=module.Sparse(game,data,1,True,True,10000,1000000);nodes=[];start=time.monotonic()
    def build(states):
        if len(nodes)>2000 or time.monotonic()-start>10:raise ValueError('finite oracle build cap')
        for w,state in enumerate(states):
            while state.is_chance_node() and not state.is_terminal():state.apply_action(decks[w][4+len(state.audit()['board'])])
        k=len(nodes)
        if states[0].is_terminal():nodes.append(dict(actor=-1,children=[],utility=np.array([s.returns() for s in states])/2));return k
        obs=[observation(s) for s in states];p=obs[0].actor;acts=obs[0].actions;shared=[]
        for o in obs:
            r=core.query(o.own,o.board,o.actor,o.round,o.history,o.actions,o.live,o.street,o.remaining,o.price,True);shared.append(r['key'].hex())
        n=dict(actor=p,actions=acts,keys=[o.key for o in obs],compact=shared,children=[]);nodes.append(n)
        for action in acts:
            children=[clone_native(native,game,decks[w],s) for w,s in enumerate(states)]
            for s in children:s.apply_action(action)
            n['children'].append(build(children))
        return k
    states=[]
    for deck in decks:
        state=native.NativeState(game)
        for c in deck[:4]:state.apply_action(c)
        states.append(state)
    build(states)
    import copy
    def trainer(compact):
        q=Joint.__new__(Joint);q.N=2;q.W=len(decks);q.weights=np.full(q.W,1/q.W);q.nodes=copy.deepcopy(nodes);q.actions={};q.owners={};q.t=0
        for n in q.nodes:
            if n['actor']<0:continue
            if compact:n['keys']=n['compact']
            for key in n['keys']:q.actions[key]=n['actions'];q.owners[key]=n['actor']
        q.R={k:np.zeros(len(v)) for k,v in q.actions.items()};q.A={k:v.copy() for k,v in q.R.items()};return q
    full=trainer(False);compact=trainer(True);pi=full.policy();oracle=path_oracle(full,pi);max_error=max(abs(oracle['EV']-full.weights@full.values(pi)[0]));full.step()
    max_error=max(max_error,max(float(np.max(abs(full.R[k]-np.maximum(0,v)))) for k,v in oracle['grad'].items()),max(float(np.max(abs(full.A[k]-v))) for k,v in oracle['avg'].items()))
    curves=[];began=time.monotonic()
    for target in (0,16,64,256):
        while compact.t<target:
            if time.monotonic()-began>15:raise ValueError('finite oracle training cap')
            compact.step()
        cpi=compact.policy();projected={}
        for n in nodes:
            if n['actor']>=0:
                for actual,coarse in zip(n['keys'],n['compact']):projected[actual]=cpi[coarse]
        ev=full.weights@full.values(projected)[0];br=[full.br(projected,p) for p in (0,1)];ind=[path_br(full,projected,p) for p in (0,1)];max_error=max(max_error,max(abs(a-b) for a,b in zip(br,ind)))
        curves.append(dict(iterations=compact.t,EV_bb=ev.tolist(),full_finite_BR_bb=br,full_finite_NashConv_bb=float(sum(br)),scope='all native actions in6chipHU /8 explicit worlds; not HU50 or uniform52 bound'))
    collisions=sum(len(set(n['keys']))>len(set(n['compact'])) for n in nodes if n['actor']>=0)
    atomic(out,dict(decks=decks,stacks=[6,6],nodes=len(nodes),full_infosets=len(full.actions),compact_infosets=len(compact.actions),colliding_public_nodes=collisions,independent_path_max_error=max_error,curve=curves,seconds=time.monotonic()-start,source_sha256=sha(Path(__file__)),native_binary_sha256=sha(Path(native.__file__)),abstraction_global_error_upper=None,formal_pass=False))
