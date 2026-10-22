"""Bounded fresh-database startup stress; never accepts a retained DB path."""
import argparse
import importlib.util
import json
from pathlib import Path
import select
import sqlite3
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('owned_stress_worker', ROOT / 'scripts/code_worker.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
CHILD = '''
import importlib.util,sys
spec=importlib.util.spec_from_file_location('owned_worker',sys.argv[1])
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
print('loaded',flush=True)
sys.stdin.readline()
leases=w.Leases(sys.argv[2])
try:
    assert leases.claim({'id':'owned-'+sys.argv[3],'lane':'isolated-'+sys.argv[3]},now=100)
finally:
    leases.close()
print('claimed',flush=True)
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rounds', type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.rounds <= 20:
        parser.error('rounds must be 1..20')
    for generation in range(args.rounds):
        children = []
        with tempfile.TemporaryDirectory(prefix='pokerid-owned-startup-') as directory:
            state = Path(directory) / 'fresh.sqlite'
            try:
                for index in range(8):
                    children.append(subprocess.Popen(
                        [sys.executable, '-B', '-c', CHILD,
                         str(ROOT / 'scripts/code_worker.py'), str(state), str(index)],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        text=True, env=worker.child_env()))
                for child in children:
                    assert select.select([child.stdout], [], [], 10)[0], 'child startup timeout'
                    assert child.stdout.readline().strip() == 'loaded', 'child did not reach barrier'
                for child in children:
                    child.stdin.write('start\n')
                    child.stdin.flush()
                for child in children:
                    output, error = child.communicate(timeout=15)
                    assert child.returncode == 0, error
                    assert output.strip() == 'claimed'
                db = sqlite3.connect(state)
                try:
                    assert db.execute('PRAGMA journal_mode').fetchone()[0] == 'wal'
                    assert db.execute('SELECT COUNT(*) FROM development_jobs').fetchone()[0] == 8
                    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
                finally:
                    db.close()
            finally:
                for child in children:
                    if child.poll() is None:
                        child.kill()
                        child.communicate(timeout=5)
    print(json.dumps({'rounds': args.rounds, 'processes_per_round': 8,
                      'successful_initializers': args.rounds * 8,
                      'owned_databases_only': True, 'result': 'PASS'}))


if __name__ == '__main__':
    main()
