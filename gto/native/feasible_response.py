"""Information-set-feasible full-continuation response research, not a certificate.

Strict snapshots stay strict. Completing their missing rows is an explicit,
separately identified total-profile experiment. Its EV is NOT the EV of the
original partial learned strategy. A tested feasible deviation gives only a
LOWER bound against that completed profile; a failed candidate proves nothing
about equilibrium or the optimum best response.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib,json,math,random
from pathlib import Path
from gto.hand169 import CLASSES,hand_class
from gto.native.hand169_bridge import card_name
from gto.native.infoset_export import PolicySnapshot,_digest
from gto.native.history_reach import _strategy
from gto.native.training import checkpoint


@dataclass(frozen=True)
class CompletedPolicy:
    snapshot: PolicySnapshot
    completion: str
    key_mode: str = 'native'
    def __post_init__(self):
        if (type(self.snapshot) is not PolicySnapshot or self.completion!='uniform_legal_prior'
                or self.key_mode not in ('native','unordered_own_cards')):
            raise ValueError('explicit immutable uniform-prior completion declaration required')
    @property
    def digest(self):return _digest({'snapshot':self.snapshot.digest,'completion':self.completion,'key_mode':self.key_mode})
    def decide(self,node):
        if self.key_mode=='native':row=self.snapshot.observed_row(node)
        else:
            if node.is_terminal() or node.is_chance_node():raise ValueError('hero decision required')
            row=self.snapshot._rows.get(unordered_hero_key(node.information_state_string(node.current_player())))
            if row is not None:
                if set(row)!=set(node.legal_actions()):raise ValueError('response actions differ')
                row=dict(row)
        if row is not None:return row,False
        actions=node.legal_actions()
        if not actions:raise ValueError('legal decision required')
        return {a:F(1,len(actions)) for a in actions},True
    def __call__(self,node):return self.decide(node)[0]


def unordered_hero_key(key):
    # Own-card DEAL ORDER is private, payoff-irrelevant and invisible to the
    # fixed opponent. No suit/rank/board abstraction or action pruning occurs.
    info=json.loads(key);info['hand']=sorted(info['hand'])
    return json.dumps(info,sort_keys=True,separators=(',',':'))


class LockedState:
    """Only hero decisions are learner decisions; opponent is fixed chance."""
    def __init__(self,node,hero,opponent):self.node=node;self.hero=hero;self.opponent=opponent
    def is_terminal(self):return self.node.is_terminal()
    def is_chance_node(self):
        return not self.is_terminal() and (self.node.is_chance_node() or self.node.current_player()!=self.hero)
    def current_player(self):return -4 if self.is_terminal() else -1 if self.is_chance_node() else 0
    def information_state_string(self,player):
        if player!=0 or self.is_terminal() or self.is_chance_node():raise ValueError('hero information only')
        return unordered_hero_key(self.node.information_state_string(self.hero))
    def legal_actions(self):
        if self.is_chance_node() or self.is_terminal():raise ValueError('hero decision required')
        return self.node.legal_actions()
    def chance_outcomes(self):
        if self.node.is_chance_node():return self.node.chance_outcomes()
        if not self.is_chance_node():raise ValueError('chance required')
        row=_strategy(self.node,self.opponent);result=[(a,float(p)) for a,p in row.items() if p]
        # Generic solver chance uses binary64. Close its cumulative distribution;
        # held-out evaluation below samples the exact rational frozen policy.
        partial=sum(p for _,p in result[:-1]);last=1-partial
        if last < -1e-12 or abs(last-result[-1][1])>1e-12:raise ValueError('chance rounding exceeds budget')
        result[-1]=(result[-1][0],max(0.,last))
        return result
    def apply_action(self,action):self.node.apply_action(action)
    def player_return(self,player):
        if player!=0 or not self.is_terminal():raise ValueError('hero terminal utility required')
        return self.node.returns()[self.hero]


class LockedOpponentGame:
    def __init__(self,native,game,hero,opponent):
        from gto.native.initial_chance_reach import _verified_game
        _verified_game(game)
        if game.num_players()!=2 or type(hero) is not int or hero not in (0,1) or type(opponent) is not CompletedPolicy:
            raise ValueError('HU frozen-opponent game required')
        self.native=native;self.original=game;self.hero=hero;self.opponent=opponent
        self._public_config_json=json.dumps({'model':'single-updater-frozen-opponent-v1','hero':hero,
            'hero_key_mode':'unordered_own_cards',
            'native_config':json.loads(game._public_config_json),'opponent_digest':opponent.digest},sort_keys=True,separators=(',',':'))
    def num_players(self):return 1
    def new_initial_state(self):return LockedState(self.native.NativeState(self.original),self.hero,self.opponent)


def response_snapshot(solver):
    if solver.stats()['native_engine'] or not solver.stats()['healthy']:raise ValueError('healthy locked-opponent generic solver required')
    before=(solver.iteration,solver.rng_state());keys=tuple(solver.keys());rows={}
    for key in keys:
        row=solver.row(key)
        if row['updates']<=0:continue
        values=[F(v) for v in row['average']];total=sum(values)
        if total<=0 or any(v<0 for v in values):raise ValueError('invalid updated response policy')
        rows[key]={a:v/total for a,v in zip(row['actions'],values)}
    if before!=(solver.iteration,solver.rng_state()) or tuple(solver.keys())!=keys:
        raise ValueError('response changed during freeze')
    return PolicySnapshot(rows,max_rows=1000000)


def moments_interval(total,squared,n,lo,hi,failure):
    """Fixed-n intersection of Hoeffding and empirical-Bernstein intervals."""
    if (type(n) is not int or n<0 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (total,squared,lo,hi,failure))
            or not lo<hi or not 0<failure<1 or squared<0
            or n and (not n*lo<=total<=n*hi or n*squared<total*total)
            or not n and (total!=0 or squared!=0)):
        raise ValueError('bounded fixed-sample moments required')
    if not n:return {'samples':0,'mean':None,'interval':[lo,hi]}
    mean=total/n;span=hi-lo
    hoeff=span*math.sqrt(math.log(4/failure)/(2*n))
    variance=max(0.,(squared-total*total/n)/(n-1)) if n>1 else 0.
    bern=(math.sqrt(2*variance*math.log(8/failure)/n)+7*span*math.log(8/failure)/(3*(n-1))) if n>1 else math.inf
    radius=math.nextafter(min(hoeff,bern),math.inf)
    return {'samples':n,'mean':mean,'interval':[max(lo,math.nextafter(mean-radius,-math.inf)),
        min(hi,math.nextafter(mean+radius,math.inf))], 'sample_variance':variance,
        'method':'fixed-n Hoeffding/empirical-Bernstein intersection; split failure budget'}


def _ticket(row,rng):
    denominator=math.lcm(*(p.denominator for p in row.values()));ticket=rng.randrange(denominator)
    for action,p in row.items():
        ticket-=p.numerator*(denominator//p.denominator)
        if ticket<0:return action
    raise ValueError('policy not normalized')


def terminal_trajectory(native,game,cards,action_seed,base,response=None,hero=0):
    node=native.NativeState(game)
    for card in cards[:4]:node.apply_action(card)
    offset=4;rng=random.Random(action_seed);counts={'observed':0,'completed':0,'postflop_decisions':0}
    for _ in range(1000):
        if node.is_terminal():
            result=node.settlement();net=result['net'];rake=result['rake']
            if len(net)!=2 or sum(net)!=-rake or any(type(v) is not int or not -game.stacks[i]<=v<=sum(game.stacks)-game.stacks[i] for i,v in enumerate(net)):
                raise ValueError('native settlement/chip conservation differs')
            return net,counts
        if node.is_chance_node():node.apply_action(cards[offset]);offset+=1;continue
        actor=node.current_player();policy=response if response is not None and actor==hero else base
        row,completed=policy.decide(node)
        counts['completed' if completed else 'observed']+=1
        # The audit is for diagnostics only, never an input to policy decisions.
        if node.audit()['round']>0:counts['postflop_decisions']+=1
        node.apply_action(_ticket(row,rng))
    raise ValueError('real continuation step limit; no partial EV returned')


def evaluate(native,game,base,response,*,hero=0,samples=12000,seed=100017,confidence=.99):
    from gto.native.initial_chance_reach import _verified_game
    _verified_game(game)
    if (game.num_players()!=2 or type(hero) is not int or hero not in (0,1)
            or type(samples) is not int or not 2<=samples<=100000
            or type(seed) is not int or not 0<confidence<1
            or type(base) is not CompletedPolicy or type(response) is not CompletedPolicy):
        raise ValueError('fixed declared HU held-out evaluation required')
    groups={label:[[0,0,0] for _ in range(3)] for label in CLASSES};global_moments=[[0,0,0] for _ in range(3)]
    usage=[{'observed':0,'completed':0,'postflop_decisions':0} for _ in range(2)]
    rng=random.Random(seed);bb=json.loads(game._public_config_json)['rules']['bb'];trajectory_hash=hashlib.sha256()
    for _ in range(samples):
        cards=list(range(52));rng.shuffle(cards);action_seed=rng.getrandbits(128)
        a,ac=terminal_trajectory(native,game,cards,action_seed,base,hero=hero)
        b,bc=terminal_trajectory(native,game,cards,action_seed,base,response,hero)
        trajectory_hash.update(json.dumps([cards,action_seed,a,b],separators=(',',':')).encode())
        label=hand_class([card_name(c) for c in cards[2*hero:2*hero+2]])
        for moments in (global_moments,groups[label]):
            for row,value in zip(moments,(a[hero],b[hero],b[hero]-a[hero])):
                row[0]+=value;row[1]+=value*value;row[2]+=1
        for total,increment in zip(usage,(ac,bc)):
            for key in total:total[key]+=increment[key]
    failure=(1-confidence)/(3*(len(CLASSES)+1));low=-game.stacks[hero];high=sum(game.stacks)-game.stacks[hero]
    def stats(rows):
        result={}
        for name,row,bounds in zip(('base','response','gain'),rows,((low,high),(low,high),(low-high,high-low))):
            data=moments_interval(row[0],row[1],row[2],*bounds,failure)
            data.update(sum_chips=row[0],sum_squared_chips=row[1])
            data['mean_bb']=data.pop('mean')/bb if row[2] else None
            data['interval_bb']=[v/bb for v in data.pop('interval')];data.pop('sample_variance',None)
            result[name]=data
        return result
    aggregate=stats(global_moments)
    return {'schema':'pokerid-feasible-response-v1','hero':hero,'config_digest':_digest(json.loads(game._public_config_json)),
        'base_digest':base.digest,'response_digest':response.digest,'samples':samples,'seed':seed,'confidence':confidence,
        'global':aggregate,'hands':{label:stats(rows) for label,rows in groups.items()},'completion_usage':usage,
        'best_response_gain_lower_bb':max(0.,aggregate['gain']['interval_bb'][0]),
        'complete_169_sample_coverage':all(rows[0][2] for rows in groups.values()),
        'original_partial_policy_ev':None,'full_game_convergence_verified':False,
        'trajectory_sha256':trajectory_hash.hexdigest(),'config':json.loads(game._public_config_json),
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope':'complete explicitly declared profile only; feasible response gain is a lower bound, not exact best response/exploitability',
        'assumptions':'fixed held-out sample size, independent uniform card/action PRNG model; selected response fixed before evaluation'}


def experiment(native,game,policy,output,*,base_checkpoint_sha256=None,base_iteration=None):
    root=Path(output);root.mkdir(exist_ok=False);base=CompletedPolicy(policy,completion='uniform_legal_prior')
    locked=LockedOpponentGame(native,game,0,base);solver=native.Solver(locked,.6,701,True,True,.1)
    contract='pokerid-frozen-opponent-response-v1:'+_digest({'game':json.loads(locked._public_config_json),
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    observations=[]
    for iteration in (1000,10000):
        for _ in range(iteration-solver.iteration):solver.run_iteration()
        path=root/f'response-{iteration}.bin';checkpoint(solver,path,contract)
        frozen=response_snapshot(solver)
        observations.append({'iteration':iteration,'policy_digest':frozen.digest,'updated_infosets':len(frozen._rows),
            'checkpoint_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    response=CompletedPolicy(frozen,completion='uniform_legal_prior',key_mode='unordered_own_cards')
    report=evaluate(native,game,base,response)
    report['training']={'seed':701,'opponent_digest':base.digest,'observations':observations,'contract':contract,
        'base_native_iteration':base_iteration,'base_checkpoint_sha256':base_checkpoint_sha256,
        'method':'single-updater outcome MCCFR, opponent actions fixed chance, actual native continuation',
        'training_opponent_chance_precision':'binary64; held-out categorical draws use exact rational policy'}
    (root/'heldout.json').write_text(json.dumps(report,sort_keys=True)+'\n')
    print('FEASIBLE_RESPONSE '+json.dumps(report,sort_keys=True),flush=True)
    return report
