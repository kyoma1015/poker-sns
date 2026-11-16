"""Full-history response boundary. No strategy quality or registry admission implied.

Providers receive only acting player's cards and the public ledger. Missing rows
are errors, never an implicit fold. Frozen evaluation Profile is left unchanged.
"""
from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from gto.qualification.policy import legal


@dataclass(frozen=True)
class Observation:
    actor: int
    own: tuple
    board: tuple
    round: int
    price: int
    last_full: int
    remaining: tuple
    street: tuple
    live: tuple
    dead: tuple
    folded: tuple
    history: tuple
    actions: tuple

    @property
    def key(self):
        # Public history is not projected to a nearby abstract size/node.
        return json.dumps(asdict(self), sort_keys=True, separators=(',', ':'))


def observe(betting, own, board):
    actions = tuple(legal(betting))
    if not actions:
        raise ValueError('decision observation required')
    own, board = tuple(sorted(own)), tuple(board)
    cards = own + board
    if (len(own) != 2 or len(board) != (0, 3, 4, 5)[betting.round]
            or any(type(c) is not int or not 0 <= c < 52 for c in cards)
            or len(set(cards)) != len(cards)):
        raise ValueError('invalid own/public cards')
    return Observation(betting.actor, own, board, betting.round, betting.price,
                       betting.last_full, tuple(betting.remaining),
                       tuple(betting.street), tuple(betting.live),
                       tuple(betting.dead), tuple(betting.folded),
                       tuple(tuple(h) for h in betting.history), actions)


class MissingResponse(ValueError):
    pass


class PublicResponse:
    """Caller must pin game/rules and provider artifact identity for each policy.

    Provider is a callable Observation -> {native action id: probability} or None.
    Zero-probability legal actions may be omitted. Illegal/duplicate aliases,
    NaN and non-normalized rows are rejected, never clipped or renormalized.
    """
    def __init__(self, provider, *, game_digest, provider_digest):
        for digest in (game_digest, provider_digest):
            if (not isinstance(digest, str) or len(digest) != 64
                    or any(c not in '0123456789abcdef' for c in digest)):
                raise ValueError('explicit SHA-256 identities required')
        self.provider = provider
        self.identity = dict(schema='full-public-response-v1',
                             game_sha256=game_digest, provider_sha256=provider_digest,
                             implementation_sha256=hashlib.sha256(
                                 Path(__file__).read_bytes()).hexdigest())
        self.digest = hashlib.sha256(json.dumps(self.identity, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()

    def row(self, betting, own, board):
        observation = observe(betting, own, board)
        weights = self.provider(observation)
        if weights is None:
            raise MissingResponse(observation.key)
        if not isinstance(weights, dict) or not weights:
            raise ValueError('explicit nonempty response required')
        if any(type(a) is not int or a not in observation.actions for a in weights):
            raise ValueError('illegal response action')
        if any(isinstance(w, bool) or not isinstance(w, (int, float, Fraction))
               or not math.isfinite(w) or w < 0 for w in weights.values()):
            raise ValueError('invalid response probability')
        if not math.isclose(math.fsum(weights.values()), 1, rel_tol=0, abs_tol=1e-12):
            raise ValueError('response must sum to one')
        return tuple((a, weights.get(a, 0)) for a in observation.actions)
