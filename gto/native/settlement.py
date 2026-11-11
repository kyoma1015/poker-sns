"""Hand-derived synthetic settlement checks against preserved Python/C++ kernels.

No G11 historical baseline or approved house rule profile is implied. No solver
source is modified. The native bridge binds the exact original embedded Ledger.
"""
import argparse
import base64
from contextlib import contextmanager
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import sysconfig
import tempfile
import uuid
import zlib

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / 'gto/fixtures/settlement-v1.json'
REFERENCE_SHA = '456225cf675a1b8ecf9ac7b16b7e3b6185900fe3dea75fe8f1687ad12354ea5a'
HEADER_SHA = '870b64c0253be86ef139d0c2437d202d9d4f10097e871dd8bde526402dd49353'
STATE_FIELDS = ('n', 'round', 'actor', 'done', 'price', 'last_full', 'initial',
                'remaining', 'live', 'dead', 'street', 'seen', 'folded')


class SettlementMismatch(AssertionError):
    pass


def equal(label, actual, expected):
    if actual != expected:
        raise SettlementMismatch(f'{label}: actual={actual!r}, expected={expected!r}')


@contextmanager
def reference_module():
    encoded = ROOT / 'handoff/gto/compressed/pokerid_rules.py.zlib.b64'
    raw = zlib.decompress(base64.b64decode(encoded.read_text('ascii').strip(), validate=True))
    if hashlib.sha256(raw).hexdigest() != REFERENCE_SHA:
        raise ValueError('transferred Python reference SHA mismatch')
    with tempfile.TemporaryDirectory(prefix='gto-settlement-reference-') as directory:
        path = Path(directory) / 'pokerid_rules.py'; path.write_bytes(raw)
        name = 'pokerid_rules_fixture_' + uuid.uuid4().hex
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
            yield module
        finally:
            sys.modules.pop(name, None)


def rules_for(reference, base, case):
    params = {**base, **case['overrides']}
    params['rake_rate'] = Fraction(params['rake_rate'])
    rules = reference.Rules(**params)
    manifest = rules.manifest()
    native = {key: value for key, value in manifest.items() if key != 'version'}
    native.update(rate_num=rules.rake_rate.numerator, rate_den=rules.rake_rate.denominator)
    return rules, native


def python_state(game):
    return {key: [-1 if x is None else x for x in game.seen] if key == 'seen'
            else getattr(game, key) for key in STATE_FIELDS}


def projected(result):
    return {**result, 'pot_amounts': [pot['amount'] for pot in result['pots']],
            'pot_rakes': [pot['rake'] for pot in result['pots']]}


def run_case(reference, base, case, native_module=None):
    rules, native_rules = rules_for(reference, base, case)
    game = reference.Betting(case['stacks'], rules)
    native = native_module.Ledger(case['stacks'], native_rules) if native_module else None
    steps = 0
    def compare():
        if native:
            equal(case['id'] + '/state', {key: native.audit()[key] for key in STATE_FIELDS}, python_state(game))
            equal(case['id'] + '/legal', native.legal(), game.legal())
    def action(value):
        nonlocal steps
        compare()
        if value not in game.legal(): raise ValueError(case['id'] + ': fixture contains illegal action')
        game.act(value)
        if native: native.act(value)
        steps += 1
        compare()
    compare()
    for value in case['actions']: action(value)
    while not game.done:
        if steps > 100: raise ValueError('fixture action budget exceeded')
        if game.actor is not None: action(1)
        else:
            game.next_round()
            if native: native.next_round()
            steps += 1
            compare()
    result = game.settle(case['ranks'], case['flop_seen'])
    actual = projected(result)
    for key, expected in case['expected'].items():
        equal(case['id'] + '/expected/' + key, actual[key], expected)
    equal(case['id'] + '/chip-conservation', sum(result['net']), -result['rake'])
    if native:
        observed = native.settle(case['ranks'], case['flop_seen'])
        equal(case['id'] + '/native-vs-reference', observed, result)
        for key, expected in case['expected'].items():
            equal(case['id'] + '/native-expected/' + key, projected(observed)[key], expected)
    return {'id': case['id'], 'status': 'PASS', 'steps': steps,
            'net': result['net'], 'rake': result['rake'], 'refund': result['refund'],
            'native_compared': native is not None}


def run_fixture_suite(native_module=None):
    fixture = json.loads(FIXTURES.read_text())
    if fixture['schema'] != 'pokerid-synthetic-settlement-v1': raise ValueError('unsupported fixture schema')
    if not isinstance(fixture.get('cases'), list) or not fixture['cases']:
        raise ValueError('settlement fixtures require a nonempty list of cases')
    for case in fixture['cases']:
        if not isinstance(case.get('expected'), dict) or not case['expected']:
            raise ValueError('settlement cases require nonempty expected results')
        expected = case['expected']
        if 'rake' in expected and type(expected['rake']) is not int:
            raise ValueError('rake expectation requires an exact integer')
        for field in ('refund', 'net', 'pot_amounts', 'pot_rakes'):
            if field in expected and (not isinstance(expected[field], list)
                                      or any(type(value) is not int for value in expected[field])):
                raise ValueError('vector chip expectations require lists of exact integers')
    ids = [case['id'] for case in fixture['cases']]
    if len(ids) != len(set(ids)): raise ValueError('duplicate fixture ids')
    with reference_module() as reference:
        results = [run_case(reference, fixture['base_rules'], case, native_module) for case in fixture['cases']]
    return {'status': 'PASS', 'case_count': len(results), 'provenance': fixture['provenance'],
            'reference_sha256': REFERENCE_SHA, 'native_header_sha256': HEADER_SHA if native_module else None,
            'historical_baseline_used': False, 'results': results}



def validate_rank7_cards(cards):
    """Fail before either preserved kernel: Python's original omits range checks."""
    if not isinstance(cards, (list, tuple)) or len(cards) != 7:
        raise ValueError('seven distinct integer cards required')
    if any(type(card) is not int or not 0 <= card < 52 for card in cards):
        raise ValueError('cards must be integers in 0..51')
    if len(set(cards)) != 7:
        raise ValueError('seven distinct integer cards required')
    return list(cards)


def run_rank7_case(reference, case, native_module=None):
    cards = validate_rank7_cards(case['cards'])
    expected = case['expected']
    if not isinstance(expected, list) or not expected or any(type(x) is not int for x in expected):
        raise ValueError('explicit integer rank tuple required')
    observed = list(reference.rank7(cards))
    equal(case['id'] + '/python-rank7', observed, expected)
    if native_module is not None:
        equal(case['id'] + '/native-rank7', list(native_module.rank7(cards)), expected)
    return {'id': case['id'], 'status': 'PASS', 'rank': observed,
            'native_compared': native_module is not None}


def run_rank7_fixture_suite(native_module=None):
    fixture = json.loads((ROOT / 'gto/fixtures/rank7-v1.json').read_text())
    if fixture['schema'] != 'pokerid-synthetic-rank7-v1' or not fixture['cases']:
        raise ValueError('nonempty rank7 fixture required')
    ids = [case['id'] for case in fixture['cases']]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate rank7 fixture ids')
    with reference_module() as reference:
        results = [run_rank7_case(reference, case, native_module) for case in fixture['cases']]
    if {result['rank'][0] for result in results} != set(range(9)):
        raise ValueError('all nine hand categories required')
    return {'status': 'PASS', 'case_count': len(results), 'results': results,
            'provenance': fixture['provenance'], 'historical_baseline_used': False,
            'strategy_or_convergence_proof': False}

def build_and_run(native_root, compiler):
    native_root = native_root.resolve()
    include = native_root / 'g12_next'
    header = include / 'g11_rules_embed.h'
    if hashlib.sha256(header.read_bytes()).hexdigest() != HEADER_SHA:
        raise ValueError('native embedded header SHA mismatch')
    out = native_root / 'settlement-probe'; out.mkdir(exist_ok=False)
    command = [compiler, '-O2', '-std=c++20', '-fno-fast-math', '-ffp-contract=off', '-fPIC', '-shared',
               str(ROOT / 'gto/native/settlement_probe.cc'), '-I' + str(include),
               '-I' + str(native_root / 'dependencies/pybind11/pybind11/include'),
               '-I' + sysconfig.get_paths()['include'], '-o',
               str(out / ('pokerid_settlement_probe' + sysconfig.get_config_var('EXT_SUFFIX')))]
    if sys.platform == 'darwin': command += ['-undefined', 'dynamic_lookup']
    result = subprocess.run(command, capture_output=True, text=True)
    (out / 'build.txt').write_text(result.stdout + result.stderr)
    if result.returncode: raise RuntimeError('settlement bridge build failed; see ' + str(out / 'build.txt'))
    sys.path.insert(0, str(out))
    import pokerid_settlement_probe
    report = run_fixture_suite(pokerid_settlement_probe)
    report['rank7'] = run_rank7_fixture_suite(pokerid_settlement_probe)
    report['build_command'] = command
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--native-root', type=Path)
    parser.add_argument('--compiler', default='c++')
    args = parser.parse_args()
    report = build_and_run(args.native_root, args.compiler) if args.native_root else run_fixture_suite()
    print(json.dumps(report, indent=2))
