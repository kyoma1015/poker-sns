"""Learned-only stopping envelopes. Unknown policy rows NEVER get an action.

These are intervals over all completions of a partial strategy, not EVs for an
invented completion or exploitability bounds. Hidden future cards may tighten
terminal-only payoff envelopes; they are never inputs to a policy decision.
"""
from collections import Counter
from fractions import Fraction as F
import hashlib,json,random
from pathlib import Path
from gto.hand169 import CLASSES,hand_class
from gto.native.hand169_bridge import card_name
from gto.native.infoset_export import PolicySnapshot,UnknownPolicyRow,_digest
from gto.native.feasible_response import _ticket,moments_interval
from gto.native.ev_audit import independent_net

class MissingRow(UnknownPolicyRow):
    def __init__(self,reason):super().__init__(reason);self.reason=reason

class CheckpointPolicy:
    """Read-only native average adapter, bound to an actual saved checkpoint."""
    def __init__(self,native,solver,checkpoint_sha256):
        if (not isinstance(solver,native.Solver) or not solver.stats()['native_engine'] or solver.disk_enabled()
            or len(checkpoint_sha256)!=64 or any(c not in '0123456789abcdef' for c in checkpoint_sha256)):
            raise ValueError('actual native in-memory checkpoint policy required')
        self.solver=solver;self.iteration=solver.iteration;self.rng=solver.rng_state()
        self.infosets=solver.stats()['infosets'];self.digest=_digest({'checkpoint_sha256':checkpoint_sha256,'policy':'owner-updated average only'})
    def validate(self,*,full=False):
        if (self.solver.iteration!=self.iteration or self.solver.rng_state()!=self.rng
            or full and (not self.solver.stats()['healthy'] or self.solver.stats()['infosets']!=self.infosets)):
            raise ValueError('strict checkpoint policy changed')
    def __call__(self,node):
        self.validate();key=node.information_state_string(node.current_player())
        try:row=self.solver.row(key)
        except IndexError:raise MissingRow('absent') from None
        if row['updates']<=0:raise MissingRow('no_owner_update')
        actions=node.legal_actions();values=[F(v) for v in row['average']];total=sum(values)
        if list(row['actions'])!=actions or total<=0 or any(v<0 for v in values):raise ValueError('native average row differs')
        return {a:v/total for a,v in zip(actions,values)}

def _net(node,config):
    actual=node.settlement()['net'];expected=independent_net(node.audit(),config)
    if actual!=expected or list(node.returns())!=expected:raise ValueError('strict terminal ledger differs')
    return actual

def unknown_envelope(node,cards,offset,config):
    low=-config['stacks'][0];high=config['stacks'][1]
    if not set(node.legal_actions())<=set((0,1)):return (low,high),'utility_span'
    outcomes=[]
    for action in node.legal_actions():
        branch=node.clone();branch.apply_action(action);i=offset
        while not branch.is_terminal() and branch.is_chance_node():branch.apply_action(cards[i]);i+=1
        if not branch.is_terminal():return (low,high),'utility_span'
        outcomes.append(_net(branch,config)[0])
    return (min(outcomes),max(outcomes)),'terminal_only_envelope'

def trajectory(native,game,policy,cards,action_seed):
    config=json.loads(game._public_config_json);node=native.NativeState(game)
    for card in cards[:4]:node.apply_action(card)
    offset=4;rng=random.Random(action_seed);known=Counter()
    for _ in range(1000):
        if node.is_terminal():
            value=_net(node,config)[0];return (value,value),'known_terminal',dict(known)
        if node.is_chance_node():node.apply_action(cards[offset]);offset+=1;continue
        street=len(node.audit()['board']);actor=node.current_player()
        try:row=policy(node)
        except UnknownPolicyRow as error:
            bounds,method=unknown_envelope(node,cards,offset,config)
            return bounds,f'unknown:seat{actor}:board{street}:{getattr(error,"reason","absent")}:{method}',dict(known)
        if set(row)!=set(node.legal_actions()) or sum(row.values())!=1 or any(not isinstance(p,F) or p<0 for p in row.values()):
            raise ValueError('strict learned row must contain all legal actions')
        known[f'seat{actor}:board{street}']+=1;node.apply_action(_ticket(row,rng))
    raise ValueError('strict trajectory budget; no partial estimate returned')

def evaluate(native,game,policy,*,samples=12000,seed=300017,confidence=.99):
    from gto.native.initial_chance_reach import _verified_game
    _verified_game(game)
    config=json.loads(game._public_config_json)
    if (game.num_players()!=2 or config['rules']['bba'] or config['rules']['rake_rate']!='0'
        or type(policy) not in (PolicySnapshot,CheckpointPolicy) or type(samples) is not int
        or not 2<=samples<=100000 or type(seed) is not int or not 0<confidence<1):
        raise ValueError('strict HU no-ante/no-rake learned-only evaluation required')
    moments={label:[[0,0,0],[0,0,0]] for label in CLASSES};global_moments=[[0,0,0],[0,0,0]]
    stops=Counter();known=Counter();rng=random.Random(seed);trace=hashlib.sha256()
    for _ in range(samples):
        cards=list(range(52));rng.shuffle(cards);action_seed=rng.getrandbits(128)
        bounds,reason,visits=trajectory(native,game,policy,cards,action_seed);stops[reason]+=1;known.update(visits)
        label=hand_class([card_name(c) for c in cards[:2]])
        for rows in (moments[label],global_moments):
            for row,value in zip(rows,bounds):row[0]+=value;row[1]+=value*value;row[2]+=1
        trace.update(json.dumps([cards,action_seed,bounds,reason,visits],sort_keys=True,separators=(',',':')).encode())
    if type(policy) is CheckpointPolicy:policy.validate(full=True)
    failure=(1-confidence)/(2*(len(CLASSES)+1));bb=config['rules']['bb'];low=-game.stacks[0];high=game.stacks[1]
    def stats(rows):
        values=[moments_interval(*row,low,high,failure) for row in rows]
        return {'samples':rows[0][2],'ev_envelope_bb':[values[0]['interval'][0]/bb,values[1]['interval'][1]/bb],
            'endpoint_means_bb':[v['mean']/bb if v['mean'] is not None else None for v in values],
            'raw_endpoint_moments':rows,'point_ev_bb':None}
    return {'schema':'pokerid-strict-partial-policy-envelope-v1','seed':seed,'samples':samples,
        'confidence':confidence,'policy_digest':policy.digest,'config_digest':_digest(config),
        'global':stats(global_moments),'hands':{label:stats(rows) for label,rows in moments.items()},
        'stopping_reasons':dict(stops),'known_decisions':dict(known),'fallback_actions':0,
        'trajectory_sha256':trace.hexdigest(),'point_ev_bb':None,'full_game_convergence_verified':False,
        'complete_169_sample_coverage':all(rows[0][2] for rows in moments.values()),
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope':'confidence envelope for every completion of partial policy; no action or EV invented at missing rows',
        'assumptions':'fixed sample size; IID uniform deck/action PRNG model; policy frozen before evaluation'}

def reconstruct(native,game,key):
    """Roundtrip a real own-information key using arbitrary compatible other holes."""
    info=json.loads(key);seat=info['seat'];own=info['hand'];board=info['board']
    if game.num_players()!=2 or info['public_config']!=json.loads(game._public_config_json):raise ValueError('HU key config differs')
    other=[c for c in range(52) if c not in own+board][:2]
    holes=own+other if seat==0 else other+own
    node=native.NativeState(game)
    for card in holes:node.apply_action(card)
    offset=0
    def deal():
        nonlocal offset
        while not node.is_terminal() and node.is_chance_node():
            if offset>=len(board):raise ValueError('key board shorter than required')
            node.apply_action(board[offset]);offset+=1
    for street,actor,raw,price,last_full in info['betting_history']:
        deal()
        if node.is_terminal() or node.audit()['round']!=street or node.current_player()!=actor:raise ValueError('key public history differs')
        node.apply_action(raw if raw in (0,1) else 3 if raw==-3 else raw+2)
    deal()
    if node.is_terminal() or node.current_player()!=seat or node.information_state_string(seat)!=key:
        raise ValueError('native information key does not roundtrip')
    return node

def diagnose(native,solver,game,*,per_street=32):
    """Census created key street/boards; bounded owner-update/key/row roundtrips."""
    before=(solver.iteration,solver.rng_state(),solver.stats()['infosets']);keys=solver.keys()
    counts=Counter();examples={n:[] for n in (0,3,4,5)}
    for key in keys:
        info=json.loads(key);street=len(info['board']);counts[str(street)]+=1
        if len(examples[street])<per_street*4:examples[street].append(key)
    del keys
    checked=Counter();owner_zero=Counter();owner_updates=Counter();bound=CheckpointPolicy(native,solver,'0'*64)
    for street,candidates in examples.items():
        for key in candidates:
            row=solver.row(key)
            if row['updates']<=0:owner_zero[str(street)]+=1;continue
            node=reconstruct(native,game,key)
            if node.legal_actions()!=row['actions']:raise ValueError('roundtrip actions differ')
            values=[F(v) for v in row['average']];total=sum(values)
            expected={a:v/total for a,v in zip(row['actions'],values)}
            actual=bound(node)
            if actual!=expected:raise ValueError('learned average lookup differs')
            checked[str(street)]+=1;owner_updates[str(street)]+=row['updates']
            if checked[str(street)]>=per_street:break
    if before!=(solver.iteration,solver.rng_state(),solver.stats()['infosets']):raise ValueError('diagnosis changed solver')
    return {'created_key_census_by_board_cards':dict(counts),'roundtrip_owner_updated_rows':dict(checked),
        'sampled_no_owner_update_rows':dict(owner_zero),'sampled_owner_update_sum':dict(owner_updates),
        'row_sample_scope':'bounded lexical examples for identity checks, not a coverage estimate',
        'native_key_actions_average_roundtrip':True,'solver_unchanged':True}
