"""HU50 reduced preflop CFR; explicit forced-check model, NOT full-game GTO."""
import argparse,copy,gzip,json,math,time
from pathlib import Path
from gto.abstract import model
from gto.qualification.native_mccfr import betting,digest
from gto.qualification.policy import act,legal,hand,sha
from gto.qualification.action_native import load_solver
from gto.qualification.build import load
from gto.qualification.evaluate import atomic
from gto.qualification.variance_study import compressed

FALLBACK=Path('docs/qa/action-baseline-20261118/baseline-reach-checkpoint.json.gz')

def tree(rules):
    nodes=[]
    def visit(b,raises,history):
        index=len(nodes)
        if b.done and any(b.folded):
            nodes.append(dict(actor=-1,value=b.settle([0,0],False)['net'][0],matched=False,actions=[],children=[]));return index
        if b.done or b.round>0:
            if b.live[0]!=b.live[1]:raise ValueError('unmatched continuation ledger')
            nodes.append(dict(actor=-1,value=b.live[0],matched=True,actions=[],children=[]));return index
        target=(6,20,100)[raises]+2 if raises<3 else None
        actions=[a for a in (0,1,target) if a is not None and a in legal(b)]
        n=dict(actor=b.actor,raises=raises,history=history,contributions=list(b.live),
               native_prefix=[list(h[:3]) for h in b.history],native_actions=actions,
               actions=['fold' if a==0 else 'call' if b.street[b.actor]<b.price else 'check' if a==1 else 'raise_to_'+str(a-2) for a in actions],children=[])
        # Native action semantics take precedence over facing/check rendering.
        n['actions']=['fold' if a==0 else ('call' if b.street[b.actor]<b.price else 'check') if a==1 else 'raise_to_'+str(a-2) for a in actions]
        nodes.append(n)
        for a,label in zip(actions,n['actions']):
            child=copy.deepcopy(b);act(child,a)
            n['children'].append(visit(child,raises+(a not in (0,1)),history+[label]))
        return index
    visit(betting(rules),0,[]);return nodes

class ReleasePolicy:
    def __init__(self,artifact,fallback):
        if artifact['fallback_policy_digest']!=fallback.policy_digest:raise ValueError('fallback digest mismatch')
        self.rules,self.native=fallback.rules,fallback.native;self.fallback=fallback
        self.artifact=artifact;self.nodes=artifact['nodes'];self.strategy=artifact['strategy']
        self.known={tuple(tuple(h) for h in n['native_prefix']):i for i,n in enumerate(self.nodes) if n['actor']>=0}
        self.id=dict(artifact['identity']);self.iteration=artifact['abstract_sample_metrics']['iterations'];self.rows={};self.coverage_scope='abstract preflop mapped rows, not full-native trained infosets'
        self._digest=digest(dict(identity=self.id,nodes=self.nodes,strategy=self.strategy,fallback=fallback.policy_digest))
        if artifact.get('policy_digest',self._digest)!=self._digest:raise ValueError('policy digest mismatch')
    def provider(self,o):return dict(zip(o.actions,self.row(o,True)))
    @property
    def policy_digest(self):return self._digest
    def row(self,o,average=False):
        if any(o.live[p]+o.remaining[p]!=100 for p in (0,1)) or any(o.dead):raise ValueError('isolated HU50 zero-ante policy only')
        if o.round>0:
            if 1 not in o.actions:raise ValueError('explicit check/call response unavailable')
            return [float(a==1) for a in o.actions]
        k=self.known.get(tuple(tuple(h[:3]) for h in o.history))
        if k is None:return self.fallback.row(o,True)
        n=self.nodes[k]
        if n['actor']!=o.actor or tuple(n['contributions'])!=o.live:raise ValueError('public ledger mismatch')
        hs=hand(o.own);weights={a:self.strategy[(k*3+j)*169+hs] for j,a in enumerate(n['native_actions'])}
        if any(a not in o.actions for a in weights):raise ValueError('illegal abstract response')
        return [weights.get(a,0.) for a in o.actions]

def load_policy(build,artifact):
    rules,native=load(build);fallback=load_solver(rules,native,FALLBACK)
    d=json.loads(gzip.decompress(Path(artifact).read_bytes()));return ReleasePolicy(d,fallback)

def generate(build,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    rules,native=load(build);nodes=tree(rules);fallback=load_solver(rules,native,FALLBACK)
    lib=model.load(model.build(out/'build'));kernel=model.kernel(lib,samples=2,seed=18118051)
    if time.monotonic()-started>45:raise RuntimeError('kernel stage budget')
    chance_counts,prob=model.chance(model.classes())
    payoff=model.payoffs(kernel,'checkdown',nodes)
    result=model.solve(lib,payoff,prob,nodes,iterations=100)
    if time.monotonic()-started>90:raise RuntimeError('generation budget; no complete receipt')
    identity=dict(schema='pokerid-reduced-preflop-research-v1',stacks_bb=[50,50],ante_bb=0,rake=0,
        raise_to_bb=[3,10,50],continuation='both check through; off-policy postflop check/call',
        off_tree_preflop='frozen full-history policy; exact history, no nearest-size mapping',
        source_sha256={str(p):sha(p) for p in (Path(__file__),Path('gto/abstract/model.py'),Path('gto/abstract/core.cc'))},
        key='exact-suit-orbit',private_chance='exact 1326*1225 compatible ordered hole deals, 169 classes',
        real_game_continuation_error_bb=None,omitted_action_error_bb=None,formal_profile=False)
    artifact=dict(identity=identity,nodes=nodes,strategy=result['strategy'],fallback_policy_digest=fallback.policy_digest,
        abstract_sample_metrics={k:result[k] for k in ('iterations','seconds','profile_sb_ev_bb','br_sb_ev_bb','br_bb_min_sb_ev_bb','abstract_nashconv_bb')},
        kernel_seed=kernel['seed'],kernel_samples_per_class_pair=2,kernel_source_sha256=digest(kernel['mean'][:169*169]),
        exact_joint_deal_count=sum(chance_counts),model_ranges=model.ranges(result,nodes),ordinary_registry_admission=False,
        status='BLOCKED_UNVERIFIED',formal_acceptance_complete=0,verified_strategy_count=0)
    policy=ReleasePolicy(artifact,fallback);artifact['policy_digest']=policy.policy_digest
    compressed(out/'strategy.json.gz',artifact)
    compressed(out/'kernel.json.gz',dict(seed=kernel['seed'],samples_per_class_pair=2,
        allin_ev_chips=kernel['mean'][:169*169],variance=kernel['variance'][:169*169],chance_counts=chance_counts,
        kernel_seconds=kernel['seconds'],native_game_error_unknown=True))
    atomic(out/'generation.json',dict(status='BLOCKED_UNVERIFIED',policy_digest=policy.policy_digest,
        kernel_seconds=kernel['seconds'],total_seconds=time.monotonic()-started,stages=list(artifact['model_ranges']),
        stage_hand_counts={k:len(v['hands']) for k,v in artifact['model_ranges'].items()},
        **artifact['abstract_sample_metrics'],ordinary_registry_admission=False,verified_strategy_count=0,
        full_native_br_upper_bb=None,full_native_nashconv_bb=None,continuation_error_upper_bb=None))
    return policy

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--out',required=True);a=p.parse_args();generate(a.build,a.out)
