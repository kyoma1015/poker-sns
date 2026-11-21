"""Fixed short factorial diagnosis, not a new strategy search or release policy."""
import argparse,copy,json,shutil,time
from pathlib import Path
from gto.abstract import matched_history as m,joint_reach as j,joint_stream as s,joint_vector as v

def run(directory):
    root=Path(directory);root.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    result=json.loads(Path('docs/qa/matched-history-20261116/results.json').read_text())
    lib=v.build(root/'vector');out=[]
    def budget():
        if time.monotonic()-start>60 or shutil.disk_usage(root).free<2*1024**3:raise ValueError('short diagnosis budget exhausted')
    for weights in ((.5,.5),(.25,.75)):
        ws=copy.deepcopy(result['worlds']);boards=sorted({tuple(w['flop']) for w in ws})
        for w in ws:w['mass']=weights[boards.index(tuple(w['flop']))]/4
        g=j.prepare(s.layout(4)[0],ws);kernel=m.Kernel(lib,g);teacher=m.Trainer(g,kernel)
        for _ in range(32):budget();teacher.step('cfr_plus')
        state=teacher.state();methods={}
        for regret_discount,average_discount in ((False,False),(True,False),(False,True),(True,True)):
            x=m.Trainer(g,kernel);x.restore(state)
            for _ in range(16):
                budget();x.t+=1;values=kernel(m.policy(g,x.R));t=x.t
                # Same simultaneous order, same new-mass weight, same inherited
                # history; isolate only regret discount and average discount.
                for i in range(len(x.R)):
                    r=x.R[i]+values['grad'][i];power=t**(1.5 if r>0 else 0)
                    x.R[i]=r*(power/(power+1) if regret_discount else 1)
                    x.S[i]=(x.S[i]+values['avg'][i])*((t/(t+1))**2 if average_discount else 1)
            methods[f'R{int(regret_discount)}S{int(average_discount)}']=m.measure(g,x.average())
            if regret_discount and average_discount:
                reference=m.Trainer(g,kernel);reference.restore(state)
                for _ in range(16):budget();reference.step('dcfr')
                assert max(abs(a-b) for field in ('R','S') for a,b in zip(x.state()[field],reference.state()[field]))<1e-12
        out.append({'board_weights':weights,'teacher_actual_iterations':32,'additional_iterations':16,'initial':m.measure(g,teacher.average()),'methods':methods})
    return {'schema':'pokerid-short-dcfr-factorial-v1','scope':'two existing tiny games only; inherited linear S retained; not population accuracy','cases':out,'seconds':time.monotonic()-start,'new_population_runs':0,'normal_GTO_added':0,'stopped_after_fixed_budget':True}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,required=True);a=parser.parse_args()
    r=run(a.directory);(a.directory/'results.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
