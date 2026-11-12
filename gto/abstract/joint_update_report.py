"""Fail-closed comparison of completed, same-game research checkpoints."""
import argparse,hashlib,json,math
from pathlib import Path
from gto.abstract import joint_updates as u,joint_stream_cache as c

def improves(new,old):return new < old-1e-8

def checked(x):
    if x.get('coverage')!=1 or x.get('evaluated_orbits')!=1755 or x.get('population_orbits')!=1755:raise ValueError('full population required')
    nc=x['restricted_nashconv_interval_bb'];sb=x['sb_br_gain_bb'];bb=x['bb_br_gain_bb'];ev=x['partial_sb_ev_bb']
    if not all(type(v) in (int,float) and math.isfinite(v) for v in [*nc,sb,bb,ev]):raise ValueError('finite numerical evidence required')
    if abs(nc[1]-nc[0])>1e-8 or min(sb,bb)<-1e-8 or abs(sb+bb-nc[1])>1e-8:raise ValueError('BR signs/normalization mismatch')
    if x.get('full_real_game_gto_verified') is not False or x.get('formal_acceptance')!=0:raise ValueError('research isolation required')
    return {'nashconv_bb':nc[1],'sb_br_gain_bb':sb,'bb_br_gain_bb':bb,'sb_ev_bb':ev,'restricted_target_pass':nc[1]<=.1,'ordinary_admission':False}

def report(folder,baseline,control):
    folder=Path(folder);b=checked(json.loads(Path(baseline).read_text()));control=checked(json.loads(Path(control).read_text()));out={'frozen_baseline':b,'historical_vanilla_uniform2':control,'methods':{},'evidence_sha256':{},'formal_acceptance':[0,12],'ordinary_GTO_added':0,'real_game_error':'UNKNOWN','external_GTO':'NOT PERFORMED'}
    registration=json.loads((folder/'registration.json').read_text())
    for method in u.METHODS:
        if registration['identities'][method]!=u.identity(method,c.population()):raise ValueError('registered method/source/game identity mismatch')
        points=[]
        for epoch in (1,2,3):
            path=folder/(method+'-epoch'+str(epoch)+'.json')
            if not path.exists():points.append({'epoch':epoch,'status':'NOT_COMPLETED'});continue
            x=json.loads(path.read_text())
            if x.get('method')!=method or x.get('epoch')!=epoch:raise ValueError('checkpoint method/epoch mismatch')
            if x.get('coverage')!=1:points.append({'epoch':epoch,'status':'PARTIAL','coverage':x['coverage']});continue
            r=checked(x);r.update(epoch=epoch,status='COMPLETE',delta_vs_frozen_bb=r['nashconv_bb']-b['nashconv_bb'],delta_vs_vanilla2_bb=r['nashconv_bb']-control['nashconv_bb'],improves_frozen=improves(r['nashconv_bb'],b['nashconv_bb']));points.append(r);out['evidence_sha256'][path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        out['methods'][method]=points
    out['all_registered_checkpoints_completed']=all(r['status']=='COMPLETE' for rows in out['methods'].values() for r in rows)
    out['selection']='No automatic adoption; all registered outcomes retained'
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--control',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.write_text(json.dumps(report(a.folder,a.baseline,a.control),sort_keys=True,indent=2)+'\n')
