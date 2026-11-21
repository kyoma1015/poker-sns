"""Read-only projection of the existing frozen policy onto registered tiny worlds.
No population evaluation or optimizer-history reconstruction is implied.
"""
import argparse, json, math
from pathlib import Path
from gto.abstract import matched_history as m, joint_stream as s, joint_reach as j
from gto.abstract import fullsupport as fs, suit_exact as old
from gto.abstract.factorial_transfer import category

def lift(g):
    fixed=json.loads((old.ROOT/'results.json').read_text())['complete_preflop_policies']['learned_small']
    teacher=json.loads(old.old.TEACHER.read_text())
    ns,mapping,leaves=s.tree(); inverse={new:old for old,new in mapping.items()}; starts=dict(leaves)
    result=[0.]*len(g['width'])
    for k,key,i in g['keys']:
        n=ns[k];count=len(n['children'])
        if n['street']=='preflop':
            row=[fixed[(inverse[k]*3+a)*169+key[0]] for a in range(count)]
        else:
            # Own physical hand/public board only; opponent cards never enter flags.
            board,signal=key
            world=next(w for w in g['worlds'] if tuple(w['flop'])==board and w['signals'][n['actor']]==signal)
            flag=fs.groups({'pairs':[world['holes'][n['actor']]],'flop':list(board)})[0]
            leaf=n['preflop_leaf'];offset=sum(8*len(x['children']) for x in ns[starts[leaf]:k])
            table=teacher['profiles']['learned_small'][str(leaf)+'|'+category(board)]
            row=table[offset+flag*count:offset+(flag+1)*count]
        if len(row)!=count or min(row)<0 or not math.isclose(sum(row),1,abs_tol=1e-10):raise ValueError('frozen projection tree/row mismatch')
        result[i:i+count]=[x/math.fsum(row) for x in row]
    return result

def compare(result):
    out=[]
    for weights in ((.5,.5),(.25,.75)):
        worlds=json.loads(json.dumps(result['worlds']));boards=sorted({tuple(w['flop']) for w in worlds})
        for w in worlds:w['mass']=weights[boards.index(tuple(w['flop']))]/4
        g=j.prepare(s.layout(4)[0],worlds);baseline=m.measure(g,lift(g))
        out.append({'board_weights':weights,'frozen_policy_on_same_tiny_game':baseline,
                    'candidate_final128':[{'teacher_iterations':c['teacher_iterations'],'methods':{name:rows[-1]['nashconv_bb'] for name,rows in c['methods'].items()}} for c in result['cases'] if c['board_weights']==list(weights)]})
    return {'scope':'SAME_REGISTERED_TINY_GAMES_ONLY_NOT_POPULATION_0_932107_COMPARISON','games':out,'population_improvement':'UNMEASURED','frozen_population_nashconv_bb':0.9321071527220774,'normal_GTO_added':0,'gate_changed':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--result',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.write_text(json.dumps(compare(json.loads(a.result.read_text())),sort_keys=True,indent=2)+'\n')
