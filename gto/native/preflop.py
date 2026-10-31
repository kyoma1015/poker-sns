"""Replay public preflop betting through the preserved native rules.

Sizes are total street contributions in chips, including posted blinds. This
adapter never caps raises at four bets or substitutes an all-in showdown for a
postflop continuation. It exposes legality, not a solved strategy.
"""
from gto.native.hand169_bridge import context_of, export_context


def decision(native, game, history, *, cards=None):
    if not isinstance(history, (list, tuple)) or any(type(a) is not int for a in history):
        raise ValueError('explicit native betting action history required')
    if game.fixture is not None or game.root_actions:
        raise ValueError('unmodified full-deck preflop game required')
    n = game.num_players()
    cards = list(range(2*n)) if cards is None else cards
    if (not isinstance(cards, (list, tuple)) or len(cards) != 2*n
            or any(type(c) is not int or not 0 <= c < 52 for c in cards)
            or len(set(cards)) != len(cards)):
        raise ValueError('distinct native hole cards for every seat required')
    state = native.NativeState(game)
    for card in cards:
        state.apply_action(card)
    for action in history:
        if state.is_terminal() or state.is_chance_node() or state.audit()['round'] != 0:
            raise ValueError('history goes beyond a preflop decision')
        state.apply_action(action)
    if state.is_terminal() or state.is_chance_node() or state.audit()['round'] != 0:
        raise ValueError('history does not end at a preflop decision')
    return state


def describe(state):
    audit = state.audit()
    if state.is_terminal() or state.is_chance_node() or audit['round'] != 0:
        raise ValueError('preflop decision required')
    raises = sum(row[2] not in (0, 1) for row in audit['history'])
    stage = ('rfi', 'vs_open', 'vs_3bet', 'vs_4bet')[raises] if raises <= 3 else 'vs_5bet_plus'
    if not raises and any(row[2] == 1 for row in audit['history']):
        stage = 'limped_pot'
    actor = state.current_player()
    return {'stage': stage, 'raises': raises, 'seat': actor,
            'context': context_of(state.information_state_string(actor)),
            'legal_actions': [{'id': a, 'kind': 'fold' if a == 0 else 'call' if a == 1
                and audit['street'][actor] < audit['price'] else 'check' if a == 1 else 'raise',
                'raise_to_chips': a-2 if a >= 4 else 1 if a == 3 else None}
                for a in state.legal_actions()],
            'strategy_convergence': 'UNKNOWN', 'ev': None}


def frequencies(solver, state, reach_weights):
    """Reuse the existing coverage-aware exporter; require explicit reach mass."""
    result = export_context(solver, describe(state)['context'], reach_weights)
    if result['actions'] != [a['id'] for a in describe(state)['legal_actions']]:
        raise ValueError('exported actions differ from native legal actions')
    result['decision'] = describe(state)
    return result


def main():
    import argparse
    import importlib
    import json
    import sys
    from pathlib import Path
    from gto.native.training import NativeGame, contract_for
    from gto.native.checkpoints import load_verified_checkpoint
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module-dir', type=Path, required=True)
    parser.add_argument('--stacks', type=int, nargs='+', required=True)
    parser.add_argument('--bb', type=int, default=2)
    parser.add_argument('--bba', type=int, default=0)
    parser.add_argument('--rake-num', type=int, default=0)
    parser.add_argument('--rake-den', type=int, default=1)
    parser.add_argument('--rake-cap', type=int)
    parser.add_argument('--history', type=int, nargs='*', default=[])
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--reach-weights', type=Path)
    args = parser.parse_args()
    if bool(args.checkpoint) != bool(args.reach_weights):
        parser.error('checkpoint and explicit reach-weights must be supplied together')
    sys.path.insert(0, str(args.module_dir.resolve()))
    native = importlib.import_module('pokerid_g12')
    game = NativeGame(args.stacks, bb=args.bb, bba=args.bba,
                      rake_num=args.rake_num, rake_den=args.rake_den, rake_cap=args.rake_cap)
    state = decision(native, game, args.history)
    report = describe(state)
    if args.checkpoint:
        solver = native.Solver(game, .6, 0, True, True, .1)
        load_verified_checkpoint(solver, args.checkpoint, contract_for(game))
        report = frequencies(solver, state, json.loads(args.reach_weights.read_text()))
    print(json.dumps(report, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
