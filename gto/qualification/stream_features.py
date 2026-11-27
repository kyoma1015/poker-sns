"""Batch equivalent of active_chance.feature; only own and visible prefix inputs."""
import ctypes as C,os,subprocess
from pathlib import Path
import numpy as np
from gto.abstract import model
_lib=None

def build():
    global _lib
    if _lib is None:
        d=Path('/tmp')/('stream-features-'+str(os.getpid()));d.mkdir(exist_ok=True);target=d/'features.so'
        subprocess.run(['c++','-O3','-std=c++17','-fno-fast-math','-ffp-contract=off','-shared','-fPIC',str(Path(__file__).with_name('stream_feature_core.cc')),'-o',str(target)],check=True)
        _lib=C.CDLL(str(target));_lib.stream_features.argtypes=[model.IP,model.IP,C.c_int,C.c_int,model.IP];_lib.stream_features.restype=C.c_int
    return _lib

def features(holes,visible):
    out=np.empty((len(holes),13),dtype=np.int32);rc=build().stream_features(model.ints(np.asarray(holes).ravel()),model.ints(visible),len(visible),len(holes),out.ctypes.data_as(model.IP))
    if rc:raise ValueError('causal feature batch')
    answer=[]
    for row in out.tolist():answer.append(tuple(row[:4])+(tuple(row[4:8]),tuple(tuple(row[9+2*j:11+2*j]) for j in range(row[8]))))
    return answer
