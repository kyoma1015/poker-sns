"""Bounded observed training throughput; toy NashConv is NOT poker convergence."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from gto.native.training import NativeGame, train_batch
from gto.native.smoke import Game, State


def benchmark(module_dir):
    sys.path.insert(0,str(Path(module_dir).resolve()))
    native=importlib.import_module('pokerid_g12')
    result={'module_sha256':hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
            'historical_checkpoint_used':False,'poker_strategy_convergence':'UNKNOWN',
            'poker':[],'toy_matching_pennies':[]}
    with tempfile.TemporaryDirectory(prefix='gto-training-benchmark-') as d:
        for players in (2,6,9):
            game=NativeGame([4]*players,bb=2,bba=2,rake_num=0,rake_den=1)
            solver=native.Solver(game,.6,17,True,True,.1)
            report=train_batch(solver,game,100,Path(d)/f'poker-{players}.bin')
            result['poker'].append({'players':players,'synthetic_stack_chips':4,
                'iterations':100,'infosets':report['infosets'],'seconds':report['seconds'],
                'iterations_per_second':100/report['seconds'],
                'checkpoint_sha256_payload':report['checkpoint']['sha256_payload']})
        solver=native.Solver(Game(),.6,17,True,True,.1)
        for total in (200,2000,20000):
            while solver.iteration<total: solver.run_iteration()
            first=State(); second=State(); second.apply_action(0)
            p=dict(solver.get_state_policy(first))[0]
            q=dict(solver.get_state_policy(second))[0]
            # Exact two-player, zero-sum matching-pennies sum of BR gains.
            result['toy_matching_pennies'].append({'iteration':total,'p0':p,'p1':q,
                'nash_conv':abs(2*p-1)+abs(2*q-1),
                'scope':'two-action hidden-move toy only; not full poker exploitability'})
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--module-dir',required=True,type=Path)
    print(json.dumps(benchmark(p.parse_args().module_dir),indent=2))
