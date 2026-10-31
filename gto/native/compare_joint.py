"""Canonical actual-native multiway proof payload for cross-variant comparison."""
import argparse
from fractions import Fraction
import importlib
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.training import NativeGame
from gto.native.joint_reach import joint_actions
from gto.native.infoset_export import PolicySnapshot,report_json


def compare(module_dir):
    sys.path.insert(0,str(Path(module_dir).resolve()))
    native=importlib.import_module('pokerid_g12')
    game=NativeGame([4]*3);solver=native.Solver(game,.6,17,True,True,.1)
    for _ in range(400):solver.run_iteration()
    snapshot=PolicySnapshot.from_solver(native,solver)
    prefix=[8,20,44]
    def policy(node):
        length=len(node.audit()['history'])
        return {prefix[length] if length<len(prefix) else 1:Fraction(1)}
    actions=joint_actions(native,NativeGame([200]*3),[48,49],
        [([[0,1],[4,5]],Fraction(1))],[],prefix,[0,1,92],policy,
        hero_seat=2,samples_per_deal=10,seed=17)
    return {'native_learned_policy_digest':snapshot.digest,'learned_iterations':400,
        'learned_seed':17,'learned_config':'three seats;4chips each;BB2;no ante/rake',
        'explicit_threeway_actions':actions,'equilibrium_verified':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module-dir',type=Path,required=True)
    print(report_json(compare(parser.parse_args().module_dir)))
