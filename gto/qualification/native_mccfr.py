"""Outcome-sampling MCCFR on the full native HU50 game. Research only.

All information sets include exact own/public observations. A uniform generative
prior defines unseen rows at every legal history; no fold completion/abstraction.
"""
import argparse
import copy
import hashlib
import json
import math
import random
import time
from pathlib import Path
from fractions import Fraction
from gto.abstract.matched_history import policy as regret_matching
from gto.qualification.build import load
from gto.qualification.policy import act, legal, sha, ROOT
from gto.qualification.public_response import observe, PublicResponse
from gto.qualification.evaluate import atomic
from gto.native.training import NativeGame

CONFIG = dict(stacks=[100, 100], bb=2, ante=0, rake=0,
              deck=52, actions='all native integer-chip raise-to', streets='all')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def identity():
    return dict(config=CONFIG, method='outcome-sampling-mccfr-v1', epsilon=.6,
                prior='uniform-all-legal-exact-history',
                sources={str(p.relative_to(ROOT)): sha(p) for p in (
                    Path(__file__), ROOT/'gto/qualification/public_response.py',
                    ROOT/'gto/abstract/matched_history.py',
                    ROOT/'gto/qualification/policy.py', ROOT/'gto/qualification/build.py',
                    ROOT/'gto/native/training.py',
                    ROOT/'handoff/gto/g12_next/g11_native_state.h',
                    ROOT/'handoff/gto/compressed/g11_rules_embed.h.zlib.b64')})


def matching(values):
    n = len(values)
    return regret_matching({'keys': [(0, None, 0)], 'nodes': [{'children': list(range(n))}]}, values)


def betting(rules, stacks=(100, 100)):
    r = rules.Rules(bb=2, ante_order='ante_first', stack_basis='before_ante',
                    dead_eligibility='all_live', rake_rate=Fraction(0), rake_cap=None,
                    no_flop_no_drop=True, cap_scope='whole_hand', rounding='floor', rake_ante=True)
    return rules.Betting(list(stacks), r)


def choose(actions, probabilities, rng):
    u = rng.random(); total = 0.
    for a, w in zip(actions, probabilities):
        total += w
        if u < total: return a
    return actions[-1]


class Solver:
    def __init__(self, rules, native, seed=1201117):
        self.rules, self.native = rules, native
        self.rng = random.Random(seed); self.rows = {}; self.iteration = 0
        self.visits = 0; self.id = identity()

    def row(self, observation, average=False):
        entry = self.rows.get(observation.key)
        if entry is None: return [1/len(observation.actions)]*len(observation.actions)
        if entry['actions'] != list(observation.actions): raise ValueError('action identity changed')
        return matching(entry['S'] if average else entry['R'])

    def provider(self, observation):
        return dict(zip(observation.actions, self.row(observation, True)))

    def snapshot(self):
        return dict(identity=self.id, iteration=self.iteration, visits=self.visits,
                    rows=copy.deepcopy(self.rows), rng=self.rng.getstate())

    def restore(self, data):
        if data['identity'] != self.id: raise ValueError('checkpoint source/game mismatch')
        def tuples(x): return tuple(tuples(v) for v in x) if isinstance(x, list) else x
        self.rows = copy.deepcopy(data['rows']); self.iteration = data['iteration']
        self.visits = data['visits']; self.rng.setstate(tuples(data['rng']))

    @property
    def policy_digest(self):
        return digest(dict(identity=self.id, rows={k: matching(v['S']) for k, v in self.rows.items()}))

    def response(self):
        return PublicResponse(self.provider, game_digest=digest(CONFIG), provider_digest=self.policy_digest)

    def trajectory(self, owner):
        deck = self.rng.sample(range(52), 9); holes=[deck[:2], deck[2:4]]
        b = betting(self.rules); records=[]; log_q=0.; log_own_q=0.; own_reach=1.
        while not b.done:
            o = observe(b, holes[b.actor], deck[4:4+(0, 3, 4, 5)[b.round]])
            pi = self.row(o); n=len(pi)
            q = [(.6/n+.4*w) for w in pi] if b.actor==owner else pi
            a = choose(o.actions, q, self.rng); index=o.actions.index(a)
            if b.actor == owner:
                # Own reach / path sampling reach estimates average-strategy sums.
                avg_weight=own_reach*math.exp(-log_q)
                records.append((o, pi, index, q[index], log_own_q, avg_weight))
                own_reach *= pi[index]; log_own_q += math.log(q[index])
            log_q += math.log(q[index]); act(b, a)
            if len(b.history)>512: raise RuntimeError('unexpected path length')
        ranks=[self.native.rank7(h+deck[4:]) for h in holes]
        utility=b.settle(ranks, b.round>=1)['net'][owner]/2
        # Suffix importance ratio sigma/q only for traverser actions. Opponent
        # sampled exactly from sigma; chance sampled from the actual deal law.
        for o, pi, delta, avg_weight in outcome_updates(records, utility):
            entry=self.rows.setdefault(o.key, dict(actions=list(o.actions), R=[0.]*len(pi), S=[0.]*len(pi)))
            for a in range(len(pi)):
                entry['R'][a] += delta[a]
                entry['S'][a] += avg_weight*pi[a]
            if not all(math.isfinite(x) for x in entry['R']+entry['S']):
                raise ArithmeticError('importance estimator overflow; do not clip')
            self.visits += 1

    def step(self):
        for owner in (0, 1): self.trajectory(owner)
        self.iteration += 1


def outcome_updates(records, utility):
    """Unbiased sampled counterfactual regret increments, no value clipping."""
    suffix=1.
    for observation, pi, index, sampling, prefix_q, avg_weight in reversed(records):
        estimate=utility*math.exp(-prefix_q)*suffix/sampling
        expected=pi[index]*estimate
        delta=[(estimate if a==index else 0.)-expected for a in range(len(pi))]
        yield observation, pi, delta, avg_weight
        suffix *= pi[index]/sampling


def rollout(solver, deck, rng, forced=None, state=None):
    b=betting(solver.rules); holes=[deck[:2], deck[2:4]]
    if state:
        for c in deck[:4]: state.apply_action(c)
    decisions=0
    while not b.done:
        if state:
            while state.is_chance_node(): state.apply_action(deck[4+len(state.audit()['board'])])
            assert state.legal_actions()==legal(b) and state.current_player()==b.actor
        if forced and decisions<len(forced): a=forced[decisions]
        else:
            o=observe(b, holes[b.actor], deck[4:4+(0,3,4,5)[b.round]])
            a=choose(o.actions, solver.row(o, True), rng)
        act(b,a)
        if state: state.apply_action(a)
        decisions+=1
        if decisions>512: raise RuntimeError('unexpected path length')
    ranks=[solver.native.rank7(h+deck[4:]) for h in holes]
    net=[v/2 for v in b.settle(ranks,b.round>=1)['net']]
    if state:
        while state.is_chance_node(): state.apply_action(deck[4+len(state.audit()['board'])])
        assert state.is_terminal() and [v/2 for v in state.returns()]==net
        assert state.audit()['history']==[list(h) for h in b.history]
    return net


def train(build, output, iterations, seconds, resume=None):
    rules,native=load(build); solver=Solver(rules,native)
    if resume: solver.restore(json.loads(Path(resume).read_text()))
    start=time.monotonic(); start_iteration=solver.iteration
    while solver.iteration<iterations and time.monotonic()-start<seconds:
        solver.step()
        if solver.iteration%32==0: atomic(output,solver.snapshot())
    atomic(output,solver.snapshot())
    return dict(policy_digest=solver.policy_digest, iteration=solver.iteration,
                new_iterations=solver.iteration-start_iteration, visited_information_sets=len(solver.rows),
                elapsed_seconds=time.monotonic()-start, algorithmically_complete_policies=1,
                qualified_policies=0, status='BLOCKED_UNVERIFIED')


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--build',required=True);p.add_argument('--output',required=True)
    p.add_argument('--iterations',type=int,default=256);p.add_argument('--seconds',type=float,default=30)
    p.add_argument('--resume');a=p.parse_args()
    print(json.dumps(train(a.build,a.output,a.iterations,a.seconds,a.resume),indent=2))
