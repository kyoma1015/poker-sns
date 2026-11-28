"""Explicit offline2..9-player profile replay. No solver or equilibrium certificate."""
import hashlib,json,math,random
from fractions import Fraction
from gto.qualification.public_response import PublicResponse
from gto.qualification.policy import act,legal
from gto.qualification.native_mccfr import choose
from gto.native.training import contract_for


def checked_config(game):
    config=json.loads(game._public_config_json);n=len(config['stacks'])
    if not 2<=n<=9 or game.stacks!=config['stacks'] or game.num_players()!=n:
        raise ValueError('explicit2..9-player native configuration required')
    rules={k:v for k,v in config['rules'].items() if k!='version'}
    rate=Fraction(rules['rake_rate']);rules.update(rate_num=rate.numerator,rate_den=rate.denominator)
    if game._native_rules!=rules or game.fixture is not None or game.root_actions:
        raise ValueError('unmodified complete native game/rules required')
    return config


class OfflineProfile:
    """Bind an explicit all-seat provider, without treating HU rows as a6/9 policy."""
    def __init__(self,game,provider,*,players,provider_digest):
        config=checked_config(game)
        if type(players) is not int or players!=len(config['stacks']) or not callable(provider):
            raise ValueError('provider must explicitly declare matching player count')
        self.game_contract=contract_for(game);self.players=players
        game_digest=hashlib.sha256(game._public_config_json.encode()).hexdigest()
        self.response=PublicResponse(provider,game_digest=game_digest,provider_digest=provider_digest)
        self.identity=dict(schema='offline-multiplayer-profile-v1',game_contract=self.game_contract,
            players=players,provider_digest=provider_digest,response_digest=self.response.digest,
            scope='all-seat fixed supplied policy; no HU transfer or equilibrium claim',
            formal_profile=False,ordinary_registry_admission=False)
    def validate_game(self,game):
        checked_config(game)
        if self.game_contract!=contract_for(game) or self.players!=game.num_players():
            raise ValueError('profile/configuration mismatch')


def replay(native,game,profile,*,deck,seed,max_steps=512):
    """Known-deck full-street replay; provider sees only own/public Observation.

    Reuses reference Betting/PublicResponse and actual native State. The settlement
    cross-check is implementation parity, not an independent rank/BR proof. Fixed
    decks are diagnostic worlds, NOT hidden-information equilibrium EV estimates.
    """
    profile.validate_game(game);config=checked_config(game);n=profile.players
    if (not isinstance(deck,(list,tuple)) or len(deck)!=52 or any(type(c) is not int for c in deck)
            or set(deck)!=set(range(52)) or type(seed) is not int
            or type(max_steps) is not int or not 1<=max_steps<=10000):
        raise ValueError('full52permutation, integer seed and bounded steps required')
    from pokerid_rules import Betting,Rules
    kwargs={k:Fraction(v) if k=='rake_rate' else v for k,v in config['rules'].items() if k!='version'}
    b=Betting(list(config['stacks']),Rules(**kwargs));s=native.NativeState(game)
    holes=[list(deck[2*p:2*p+2]) for p in range(n)]
    for card in deck[:2*n]:s.apply_action(card)
    rng=random.Random(seed);steps=0
    while not s.is_terminal():
        if steps>=max_steps:raise ValueError('step cap; no partial value returned')
        if s.is_chance_node():
            s.apply_action(deck[2*n+len(s.audit()['board'])])
        else:
            audit=s.audit();p=s.current_player()
            if b.done or p!=b.actor or legal(b)!=list(s.legal_actions()) or b.round!=audit['round']:
                raise ValueError('native/reference decision differs')
            row=profile.response.row(b,holes[p],audit['board'])
            a=choose([a for a,_ in row],[v for _,v in row],rng)
            act(b,a);s.apply_action(a)
        steps+=1
    audit=s.audit()
    if not b.done or any(list(getattr(b,k))!=list(audit[k]) for k in ('live','dead','remaining','folded')):
        raise ValueError('native/reference public ledger differs')
    ranks=[native.rank7(h+list(audit['board'])) for h in holes] if len(audit['board'])==5 else [0]*n
    settlement=b.settle(ranks,len(audit['board'])>=3);net=list(s.returns());total=sum(config['stacks'])
    if len(net)!=n or any(not math.isfinite(v) or v!=int(v) for v in net):
        raise ValueError('finite integer-chip native return required')
    net=[int(v) for v in net]
    if (net!=settlement['net'] or sum(net)!=-settlement['rake']
            or any(type(v) is not int or not -config['stacks'][p]<=v<=total-config['stacks'][p] for p,v in enumerate(net))):
        raise ValueError('native/reference settlement/conservation differs')
    return dict(players=n,net_chips=net,rake_chips=settlement['rake'],refund_chips=settlement['refund'],
        pots=settlement['pots'],board=list(audit['board']),steps=steps,profile_identity=profile.identity,
        scope='known-world supplied-profile native replay only',native_infoset_EV=None,
        complete_BR=None,NashConv=None,ordinary_registry_admission=False,formal_acceptance_complete=0)
