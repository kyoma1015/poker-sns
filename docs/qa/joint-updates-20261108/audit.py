"""Independent tiny-game learning curves and one-time native cost audit."""
import argparse,json,math,time
from pathlib import Path
from gto.abstract import joint_update_audit as a,joint_updates as u,joint_stream as s,joint_stream_cache as c

def curves():
    result={}
    for method in ('vanilla',)+u.METHODS:
        R=[[1e-15*p for p in row] for row in a.policies()];S=[[0.]*16 for _ in range(2)];points=[]
        for t in range(1,65):
            pi=[s.strategy(r,v,[(k,1,2,k) for k in range(0,16,2)],False) for r,v in zip(R,S)];outs=[a.oracle(b,p) for b,p in enumerate(pi)]
            sharedG=[sum(a.WEIGHT[b]*outs[b]['grad'][j] for b in range(2)) for j in range(8)];sharedA=[sum(a.WEIGHT[b]*outs[b]['avg'][j] for b in range(2)) for j in range(8)]
            for b in range(2):
                grad=sharedG+[a.WEIGHT[b]*x for x in outs[b]['grad'][8:]];avg=sharedA+[a.WEIGHT[b]*x for x in outs[b]['avg'][8:]]
                if method=='vanilla':R[b]=[x+y for x,y in zip(R[b],grad)];S[b]=[x+y for x,y in zip(S[b],avg)]
                else:R[b],S[b]=u.update(R[b],S[b],grad,avg,t,method)
            avgpi=[s.strategy(r,v,[(k,1,2,k) for k in range(0,16,2)],True) for r,v in zip(R,S)];ev=sum(a.WEIGHT[b]*a.oracle(b,p)['ev'] for b,p in enumerate(avgpi));br=[a.brute_br(avgpi,i) for i in (0,1)]
            points.append({'t':t,'nc':sum(br),'sb_gain':br[0]-ev,'bb_gain':br[1]+ev})
        result[method]={'points':points,'nonmonotone_steps':[x['t'] for prev,x in zip(points,points[1:]) if x['nc']>prev['nc']+1e-12]}
    return result

def cost(cache_dir,baseline_path):
    rows=c.population();store=s.Store(baseline_path,rows);full=s.build('/tmp/update-audit-full');fast=u.build('/tmp/update-audit-fast');out=[]
    for i in (0,500,1500):
        obj,values=c.read(cache_dir,rows[i]);reg,avg=store.state(i,len(obj['codes']));results={};timings={}
        for name,lib in [('full',full),('training_only',fast)]:
            start=time.process_time();results[name]=s.block(lib,obj,values,reg,avg);timings[name]=time.process_time()-start
        for key in ('grad','avg','metrics','action_num','action_den'):assert results['full'][key]==results['training_only'][key]
        grad=results['full']['grad'];positive=[abs(x) for x in grad if abs(x)>0]
        out.append({'orbit_index':i,'private_types':len(obj['codes']),'cpu_seconds':timings,'ratio_training_to_full':timings['training_only']/timings['full'],'max_abs_frozen_cf_gradient':max(positive),'max_gradient_to_epsilon_ratio':max(positive)/1e-15,'training_gradient_average_bit_equal':True})
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);aargs=p.parse_args();r={'tiny_game':curves(),'cost_samples':cost('/workspace/joint-stream-cache','/workspace/joint-stream-run/frozen.sqlite'),'warning':'Small game cost/curves are not HU50 full-population GTO accuracy'};aargs.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'nonmonotone':{k:v['nonmonotone_steps'] for k,v in r['tiny_game'].items()},'cost':r['cost_samples']}),flush=True)
