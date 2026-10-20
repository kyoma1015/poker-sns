"""Bounded native/numeric/temporary-resume tests, not G11 or full poker parity."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
import tempfile
import time
from fractions import Fraction

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from gto.native.checkpoints import load_verified_checkpoint


class Game:
    """Matching pennies: hidden first move, two player zero-sum fixture only."""
    def num_players(self): return 2
    def new_initial_state(self): return State()


class State:
    def __init__(self): self.actions = []
    def is_terminal(self): return len(self.actions) == 2
    def is_chance_node(self): return False
    def current_player(self): return len(self.actions)
    def legal_actions(self): return [0, 1]
    def information_state_string(self, player): return 'matching-pennies-player-' + str(player)
    def apply_action(self, action): self.actions.append(action)
    def player_return(self, player):
        value = 1. if self.actions[0] == self.actions[1] else -1.
        return value if player == 0 else -value


def poker_matrix(native):
    from pokerid_rules import Rules
    cases = []
    started = time.perf_counter()
    for players in range(2, 10):
        for stack_bb in range(2, 42, 2):
            for format_name in ('cash', 'mtt_chip_ev'):
                class PokerGame:
                    _g11_native_spec = True
                    def __init__(self):
                        self.stacks = [stack_bb * 2] * players
                        rate = Fraction(1, 10) if format_name == 'cash' else Fraction(0)
                        rules = Rules(bb=2, bba=2, ante_order='ante_first', stack_basis='before_ante',
                            dead_eligibility='all_live', rake_rate=rate, rake_cap=None,
                            no_flop_no_drop=True, cap_scope='whole_hand', rounding='floor', rake_ante=True)
                        manifest = rules.manifest()
                        self._native_rules = {k: v for k, v in manifest.items() if k != 'version'}
                        self._native_rules.update(rate_num=rate.numerator, rate_den=rate.denominator)
                        self.root_actions = []; self.fixture = None
                        self._public_config_json = json.dumps({'schema': 1, 'game_format': format_name,
                            'stacks': self.stacks, 'rules': manifest, 'fixture': None}, sort_keys=True, separators=(',', ':'))
                    def num_players(self): return players
                solver = native.Solver(PokerGame(), .6, 17, True, True, .1)
                solver.run_iteration()
                stats = solver.stats()
                assert solver.iteration == 1 and stats['healthy'] and stats['native_engine']
                assert math.isfinite(stats['max_abs_regret'])
                cases.append({'players': players, 'synthetic_stack_bb': stack_bb, 'format': format_name,
                              'iteration': 1, 'infosets': stats['infosets']})
    return {'status': 'PASS', 'case_count': len(cases), 'seconds': time.perf_counter() - started,
            'note': '20 synthetic equal-stack sizes 2..40bb, NOT recovered owner/G11 stack fixtures; one-iteration smoke only',
            'bb_ante': True, 'cash_rake': '1/10', 'mtt_rake': 0, 'cases': cases}


def run(module_dir, backend_file, iterations):
    sys.path.insert(0, str(module_dir))
    import pokerid_g12 as native
    spec = importlib.util.spec_from_file_location('fixture_backend', backend_file)
    backend = importlib.util.module_from_spec(spec); spec.loader.exec_module(backend)
    game = Game()
    def solver(): return native.Solver(game, .6, 17, True, True, .1)
    s = solver()
    assert s.wide and s.stats()['long_double_digits'] > 53
    assert s.test_reach_ratio([.5] * 1100, [.5] * 1100) == 1.
    assert native.test_stable_importance_ratio(1., 1e-300, 1e-300) == 1.
    for args in ((1., -1., 1.), (1., 1., 0.), (float('nan'), 1., 1.)):
        try: native.test_stable_importance_ratio(*args)
        except RuntimeError: pass
        else: raise AssertionError('invalid operands accepted')
    try: native.validate_probability_product(1e-300, 1e-300)
    except RuntimeError: pass
    else: raise AssertionError('double reach underflow not rejected')
    try: native.Solver(game, .6, 17, True, False, .1)
    except RuntimeError: pass
    else: raise AssertionError('unsupported wide=false accepted')
    started = time.perf_counter()
    for _ in range(iterations): s.run_iteration()
    elapsed = time.perf_counter() - started
    for key in s.keys():
        row = s.row(key)
        assert all(math.isfinite(x) for field in ('regret', 'average', 'current', 'baseline') for x in row[field])
        assert abs(sum(row['current']) - 1) < 1e-12
    contract = 'synthetic-matching-pennies-v1'
    with tempfile.TemporaryDirectory(prefix='gto-native-synthetic-') as directory:
        root = Path(directory)
        raw = root / 'memory.raw'
        s.save_binary(str(raw), contract)
        expected_payload = raw.read_bytes()
        memory = root / 'memory.bin'
        memory.write_bytes(expected_payload + hashlib.sha256(expected_payload).digest())
        restored = solver(); load_verified_checkpoint(restored, memory, contract)
        assert restored.iteration == s.iteration and restored.rng_state() == s.rng_state()
        assert {key: restored.row(key) for key in restored.keys()} == {key: s.row(key) for key in s.keys()}
        try: load_verified_checkpoint(solver(), memory, 'wrong-contract')
        except ValueError: pass
        else: raise AssertionError('wrong contract accepted')
        tampered = root / 'tampered-trailer.bin'
        data = bytearray(memory.read_bytes()); data[-1] ^= 1; tampered.write_bytes(data)
        # Reproduce the preserved native loader limitation; wrapper closes this path.
        unchecked = solver(); unchecked.load_binary(str(tampered), contract)
        try: load_verified_checkpoint(solver(), tampered, contract)
        except ValueError: pass
        else: raise AssertionError('wrapper accepted corrupt digest')
        database = root / 'synthetic.sqlite'
        first = backend.LiveBackend(database); disk = solver(); disk.enable_disk_backend(first, contract)
        half = iterations // 2
        for _ in range(half): disk.run_iteration()
        first.close()
        second = backend.LiveBackend(database); resumed = solver(); resumed.enable_disk_backend(second, contract)
        assert resumed.iteration == half
        for _ in range(iterations - half): resumed.run_iteration()
        exported = root / 'disk.bin'; second.export_native_checkpoint(exported, contract); second.close()
        assert exported.read_bytes() == memory.read_bytes()
        loaded = solver(); load_verified_checkpoint(loaded, exported, contract)
        assert loaded.iteration == iterations and loaded.rng_state() == s.rng_state()
        digest = hashlib.sha256(memory.read_bytes()).hexdigest()
    poker = poker_matrix(native)
    return {'status': 'PASS', 'fixture': 'synthetic matching pennies, NOT full poker/G11 reference',
            'iterations': iterations, 'infosets': len(s.keys()), 'seconds': elapsed,
            'iterations_per_second': iterations / elapsed, 'checkpoint_sha256': digest,
            'long_double_digits': s.stats()['long_double_digits'], 'python': platform.python_version(),
            'native_module': str(native.__file__), 'digest_trailer_native_check': False,
            'verified_snapshot_rejects_corruption': True, 'temporary_disk_resume_byte_equal': True,
            'historical_checkpoint_used': False, 'native_poker_matrix': poker}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--module-dir', required=True, type=Path)
    parser.add_argument('--backend', required=True, type=Path)
    parser.add_argument('--iterations', type=int, default=200)
    args = parser.parse_args()
    if not 2 <= args.iterations <= 100000: parser.error('iterations must be 2..100000')
    print(json.dumps(run(args.module_dir.resolve(), args.backend.resolve(), args.iterations), indent=2))
