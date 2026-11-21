"""Experimental exact vector kernel, independently compared to original BR.
Not substituted into any existing registered training/checkpoint.
"""
import ctypes as C,subprocess
from pathlib import Path
from gto.abstract import model

def build(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);out=directory/'joint-vector.so'
    subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(Path(__file__).with_suffix('.cc')),'-o',str(out)],check=True)
    lib=C.CDLL(str(out.resolve()));lib.stream_block.argtypes=[C.c_int]*4+[model.IP]*10+[model.DP]*11;lib.stream_block.restype=C.c_int;return lib
