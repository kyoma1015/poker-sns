import json,time,sys,resource
from gto.qualification import fullstreet_solver as f, public_chance_solver as p
from gto.qualification.build import load
from gto.qualification.evaluate import atomic
lib=p.build('/tmp/pcs');rules,_=load('/tmp/native-qualification');nodes=f.native_tree(rules);board=[0,5,10,15,20]
mode=sys.argv[1];st=time.monotonic();b=p.block(lib,board) if mode=='integrated' else f.moment(lib,board,1.);
if mode=='physical-dense':
 import numpy as np
 b=p.block(lib,board);h=b['holes'];r=b['ranks'];valid=~(h[:,None,:,None]==h[None,:,None,:]).any(axis=(2,3));b.update(mass=valid/1070190.,equity=(r[:,None]>r[None,:])+.5*(r[:,None]==r[None,:]))
setup=time.monotonic()-st
q=(p.Game if mode=='integrated' else f.Game)(lib,nodes,[b]);pi=q.policy(False);st=time.monotonic();ev=q.evaluate_owner(pi,0);elapsed=time.monotonic()-st
r=dict(mode=mode,native_nodes=len(nodes),board=board,block_seconds=setup,owner_seconds=elapsed,EV_and_BR=ev,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
atomic('docs/qa/public-chance-20261125/benchmark-'+mode+'.json',r);print(r)
