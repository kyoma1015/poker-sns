"""Finite reconstructed-G12 training batches, not original G9/G11 recovery.

No old artifacts are overwritten. The caller supplies the reconstructed native
module/game and a fresh checkpoint path. Stop is cooperative between iterations;
this module does not provide an OS watchdog or schedule a new run.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from fractions import Fraction

from gto.native.checkpoints import load_verified_checkpoint, verified_snapshot


class NativeGame:
    """Explicit native poker configuration using preserved candidate rule semantics.

    All legal native betting actions remain available (root_actions is empty).
    Supplied stacks are chips, not an invented canonical twenty-stack profile.
    """
    _g11_native_spec = True

    def __init__(self, stacks, *, bb=2, bba=0, rake_num=0, rake_den=1, rake_cap=None):
        from pokerid_rules import Rules
        if (not isinstance(stacks, (list, tuple)) or not 2 <= len(stacks) <= 9
                or any(type(s) is not int or not 0 < s <= 2**31-1 for s in stacks)
                or sum(stacks) > 2**31-1):
            raise ValueError('2..9 positive integer chip stacks required')
        if (type(bb) is not int or not 2 <= bb <= 10**9 or bb % 2
                or type(bba) is not int or not 0 <= bba <= 10**9
                or type(rake_num) is not int or type(rake_den) is not int
                or not 0 <= rake_num <= rake_den <= 10**9 or rake_den == 0):
            raise ValueError('invalid explicit blind/ante/rake configuration')
        self.stacks = list(stacks)
        rate = Fraction(rake_num, rake_den)
        if bba not in (0, bb) or rate not in (Fraction(0), Fraction(1,20), Fraction(1,10)):
            raise ValueError('native rules require 0/1BB ante and 0/5/10 percent rake')
        if rake_cap is not None and (type(rake_cap) is not int or rake_cap not in (5*bb,10*bb)):
            raise ValueError('native rake cap must be absent, 5BB or 10BB')
        rules = Rules(bb=bb, bba=bba, ante_order='ante_first', stack_basis='before_ante',
                      dead_eligibility='all_live', rake_rate=rate, rake_cap=rake_cap,
                      no_flop_no_drop=True, cap_scope='whole_hand', rounding='floor', rake_ante=True)
        manifest = rules.manifest()
        self._native_rules = {k:v for k,v in manifest.items() if k != 'version'}
        self._native_rules.update(rate_num=rate.numerator,rate_den=rate.denominator)
        self.root_actions = []
        self.fixture = None
        self._public_config_json = json.dumps({'schema':1,'stacks':self.stacks,
            'rules':manifest,'fixture':None},sort_keys=True,separators=(',',':'))

    def num_players(self):
        return len(self.stacks)


def contract_for(game):
    return 'g12-reconstructed-training-v1:' + hashlib.sha256(game._public_config_json.encode()).hexdigest()


def _fresh(path):
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise FileExistsError('output already exists; original artifacts are immutable')
    if not path.parent.is_dir():
        raise ValueError('output parent must already exist')
    return path


def checkpoint(solver, destination, contract):
    """Publish a checksummed native snapshot atomically and without overwrite.

    Exclusive hard-link publication prevents a last-moment path creation race;
    unsupported filesystems fail closed. Only fresh temporary files are removed.
    """
    destination = _fresh(destination)
    with tempfile.TemporaryDirectory(prefix='.gto-checkpoint-',dir=destination.parent) as d:
        raw, complete = Path(d)/'raw', Path(d)/'complete'
        solver.save_binary(str(raw),contract)
        digest = hashlib.sha256()
        with raw.open('rb') as source, complete.open('xb') as out:
            while chunk := source.read(1024*1024):
                digest.update(chunk); out.write(chunk)
            out.write(digest.digest()); out.flush(); os.fsync(out.fileno())
        with verified_snapshot(complete,contract) as (_,metadata):
            os.link(complete,destination)
        return metadata


def train_batch(solver, game, iterations, destination, *, resume=None, export=None, stop_check=None):
    """Run at most a finite number of real native iterations and save new output.

    Native iteration failure propagates; the original resume checkpoint remains
    untouched. It is unsafe to checkpoint a poisoned/partial native iteration.
    Stop checks occur before each iteration and once after the final iteration.
    No claim is made that a native iteration can be interrupted cooperatively.
    """
    if type(iterations) is not int or not 1 <= iterations <= 100000:
        raise ValueError('iterations must be an integer in 1..100000')
    destination = _fresh(destination)
    if export is not None:
        export = _fresh(export)
        if export == destination:
            raise ValueError('checkpoint and export must be distinct')
    if stop_check is not None and not callable(stop_check):
        raise ValueError('stop_check must be callable')
    contract = contract_for(game)
    if resume is not None:
        if solver.iteration != 0:
            raise ValueError('resume requires a fresh solver')
        load_verified_checkpoint(solver,resume,contract)
    initial = solver.iteration
    started = time.perf_counter()
    stopped = False
    for _ in range(iterations):
        if stop_check is not None and stop_check():
            stopped = True; break
        solver.run_iteration()
    if stop_check is not None and stop_check():
        stopped = True
    metadata = checkpoint(solver,destination,contract)
    if export is not None:
        with tempfile.TemporaryDirectory(prefix='.gto-export-',dir=export.parent) as d:
            temporary = Path(d)/'policies.jsonl'
            solver.export_runs(str(temporary))
            with temporary.open('rb') as f: os.fsync(f.fileno())
            os.link(temporary,export)
    stats = dict(solver.stats())
    return {'iteration':solver.iteration,'iterations_completed':solver.iteration-initial,
        'stopped':stopped,'seconds':time.perf_counter()-started,'infosets':stats['infosets'],
        'native_engine':stats['native_engine'],'checkpoint':metadata,
        'strategy_convergence':'UNKNOWN','historical_compatibility':'UNKNOWN',
        'ev_status':'not estimated by outcome MCCFR table'}


def main():
    import argparse
    import importlib
    import sys
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module-dir', required=True, type=Path)
    parser.add_argument('--stacks', required=True, type=int, nargs='+')
    parser.add_argument('--bb', type=int, default=2)
    parser.add_argument('--bba', type=int, default=0)
    parser.add_argument('--rake-num', type=int, default=0)
    parser.add_argument('--rake-den', type=int, default=1)
    parser.add_argument('--rake-cap', type=int)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--iterations', type=int, required=True)
    parser.add_argument('--checkpoint', required=True, type=Path)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--export', type=Path)
    args = parser.parse_args()
    sys.path.insert(0,str(args.module_dir.resolve()))
    native = importlib.import_module('pokerid_g12')
    game = NativeGame(args.stacks,bb=args.bb,bba=args.bba,
                      rake_num=args.rake_num,rake_den=args.rake_den,rake_cap=args.rake_cap)
    solver = native.Solver(game,.6,args.seed,True,True,.1)
    print(json.dumps(train_batch(solver,game,args.iterations,args.checkpoint,
        resume=args.resume,export=args.export),sort_keys=True,indent=2))


if __name__ == '__main__':
    main()
