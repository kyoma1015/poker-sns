"""Exact known-board integration experiment; not full-board root GTO evidence."""
import argparse
import ctypes as C
import hashlib
import json
import math
from pathlib import Path
from gto.abstract import joint_reach as joint,model,street_tree as st
from gto.abstract import call_study as cs,fullsupport as fs,suit_exact as old

ROOT=Path('docs/qa/joint-reach-20261107')

def tree():
    original=model.tree();nodes=[];mapping={};leaves=[]
    def copy(k):
        n=original[k];i=len(nodes);mapping[k]=i
        if n['actor']<0:
            if n.get('matched'):
                pot=n['value'];leaves.append((k,i))
                if pot<100:
                    subtree=st.tree(pot,50-pot/2,0,(1/3,.5,.75))['nodes']
                    for s in subtree:nodes.append({**s,'street':'flop','preflop_leaf':k,'children':[i+c for c in s['children']]})
                else:nodes.append(dict(actor=-1,children=[],c0=-50.,c1=100.,street='preflop',preflop_leaf=k))
            else:nodes.append(dict(actor=-1,children=[],c0=n['value']/2,c1=0.,street='preflop'))
        else:
            nodes.append({**n,'street':'preflop','children':[]})
            nodes[i]['children']=[copy(c) for c in n['children']]
        return i
    copy(0)
    return nodes,mapping,leaves

def worlds(build_dir,cache):
    rows=json.loads(old.DESIGN.read_text())['orbits'][:3]
    cache.mkdir(parents=True,exist_ok=True);env=None;out=[];diagnostics=[];total=sum(r['multiplicity'] for r in rows)
    for row in rows:
        path=cache/('joint-'+fs.digest(row)+'.json')
        if not path.exists():
            if env is None:env=cs.setup(build_dir)
            m=cs.exact.matrix(env[0],row['representative']);flags=fs.groups(m)
            signals=[c*8+g for c,g in zip(m['labels'],flags)];codes=sorted(set(signals));lookup={x:i for i,x in enumerate(codes)};ids=[lookup[x] for x in signals];n=len(codes);moments=(C.c_double*(2*n*n))()
            if env[1].type_aggregate(m['n'],n,n,m['cards'],model.ints(m['labels']),model.ints(ids),model.ints(ids),m['win'],m['tie'],model.doubles([1.]*169),model.doubles([1.]*169),moments):raise ValueError('unweighted fine-private chance aggregation failed')
            payload={'row':row,'codes':codes,'moments':fs.pack(moments),'method':'all compatible ordered hole pairs;all990 runouts;NO policy reach in chance'}
            path.write_text(json.dumps(payload,sort_keys=True)+'\n')
        data=json.loads(path.read_text())
        if data['row']!=row:raise ValueError('board cache identity')
        codes=data['codes'];m=fs.unpack(data['moments']);n=len(codes)
        if not math.isclose(math.fsum(m[::2]),1,abs_tol=1e-10):raise ValueError('conditional joint mass')
        if max(abs(m[(i*n+j)*2+1]+m[(j*n+i)*2+1]-m[(i*n+j)*2]) for i in range(n) for j in range(n))>1e-10:raise ValueError('zero sum showdown/card removal parity')
        for i,a in enumerate(codes):
            for j,b in enumerate(codes):
                z,e=m[(i*n+j)*2:(i*n+j)*2+2]
                if z>0:out.append(dict(flop=row['representative'],signals=(a,b),mass=z*row['multiplicity']/total,equity=e/z))
        diagnostics.append({'flop':row['representative'],'multiplicity':row['multiplicity'],'active_private_signals':n,'moment_sha256':data['moments']['sha256']})
    return out,diagnostics,total/22100

def run(build_dir,cache):
    ws,boards,coverage=worlds(build_dir,cache);ns,mapping,leaves=tree()
    print(json.dumps({'phase':'prepare','worlds':len(ws),'nodes':len(ns)}),flush=True)
    g=joint.prepare(ns,ws);s=joint.Solver(joint.build(build_dir),g)
    records=[];exports=[]
    for stop in (0,16,64,256):
        print(json.dumps({'phase':'train','checkpoint':stop}),flush=True)
        metric=s.run(stop-s.iterations);metric['policy_sha256']=hashlib.sha256(bytes(s.policy)).hexdigest();records.append(metric)
        rows=[]
        for oldnode in (0,): # Full tree export below is keyed by exact public history.
            pass
        original=model.tree()
        for k,key,offset in g['keys']:
            if ns[k]['street']!='preflop':continue
            n=ns[k];hand=model.CLASSES[key[0]];count=len(n['children'])
            rows.append({'history':n['history'],'hand':hand,'actions':n['actions'],'frequencies':list(s.policy[offset:offset+count]),'action_ev_bb':list(s.action_ev[offset:offset+count])})
        exports.append({'iterations':stop,'rows':rows})
        print(json.dumps(metric),flush=True)
    return {'schema':'joint-reach-known-board-integration-v1','protocol_sha256':hashlib.sha256((ROOT/'PROTOCOL.md').read_bytes()).hexdigest(),'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),Path(joint.__file__),Path(joint.__file__).with_suffix('.cc'))},'scope':'exact CONDITIONAL known-board-subset game; preflop values are NOT full-board root estimates; no unseen/generalization claim','boards':boards,'board_chance_subset_mass':coverage,'worlds':len(ws),'public_nodes':len(ns),'information_sets':len(g['keys']),'matched_preflop_branches':len(leaves),'chance_normalization_error':abs(math.fsum(w['mass'] for w in ws)-1),'checkpoints':records,'preflop_rows':exports,'formal_acceptance':0,'normal_GTO_ranges':0,'external_GTO':'NOT PERFORMED','real_game_approximation_error':'UNKNOWN'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--cache-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=run(a.build_dir,a.cache_dir);a.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
