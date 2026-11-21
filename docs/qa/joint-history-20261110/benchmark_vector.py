"""New exact backend parity/cost samples, not a full-population accuracy claim."""
import argparse,hashlib,json,time
from pathlib import Path
from gto.abstract import joint_vector as v,joint_stream as s,joint_stream_cache as c

def run():
    rows=c.population();store=s.Store('/workspace/joint-stream-run/frozen.sqlite',rows);old=s.build('/tmp/joint-vector-benchmark/old');new=v.build('/tmp/joint-vector-benchmark/new');out=[]
    for i in (0,500,1500):
        obj,data=c.read('/workspace/joint-stream-cache',rows[i]);reg,avg=store.state(i,len(obj['codes']));outputs={};cost={}
        for name,lib in [('original',old),('vector',new)]:
            start=time.process_time();outputs[name]=s.block(lib,obj,data,reg,avg,True);cost[name]=time.process_time()-start
        err={k:max(abs(a-b) for a,b in zip(outputs['original'][k],outputs['vector'][k])) for k in ['grad','avg','leaf','metrics','action_num','action_den']}
        if max(err.values())>=1e-8:raise ValueError(err)
        out.append({'orbit':i,'types':len(obj['codes']),'cpu_seconds':cost,'ratio':cost['vector']/cost['original'],'max_abs_error':err})
    return {'samples':out,'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(v.__file__),Path(v.__file__).with_suffix('.cc')]},'deployed_in_registered_population_run':False,'all1755parity':'NOT PERFORMED','real_game_error':'UNKNOWN'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=run();a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
