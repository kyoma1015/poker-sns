import argparse,hashlib,json,math,os,time
from pathlib import Path
from gto.abstract import joint_vector as v,joint_stream as s,joint_stream_cache as c,joint_alternating as alt,fullsupport as fs,model
FIELDS=('grad','avg','leaf','metrics','action_num','action_den')
def run(root,cpu_limit=900,wall_limit=1500):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);rows=c.population();store=s.Store('/workspace/joint-stream-run/frozen.sqlite',rows);parent=alt.numeric_digest(store.db)
 identity=fs.digest({'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(v.__file__),Path(v.__file__).with_suffix('.cc'),Path(s.__file__),Path(s.__file__).with_suffix('.cc')]},'producer':c.identity(),'population':rows,'parent_numeric_digest':parent})
 path=root/'checkpoint.json';P=store.pre;L=2*len(model.tree())*169
 if path.exists():state=json.loads(path.read_text());assert state['identity']==identity
 else:state={'identity':identity,'cursor':0,'cpu':0.,'wall':0.,'max_errors':dict.fromkeys(FIELDS,0.),'totals':{k:fs.pack([0.]*(L+3+2*P)) for k in ['original','vector']},'backend_cpu':{'original':0.,'vector':0.}}
 totals={k:fs.unpack(x) for k,x in state['totals'].items()};old=s.build(root/'old');new=v.build(root/'vector');cpu=time.process_time();wall=time.monotonic();lastcpu=cpu;lastwall=wall
 def save():
  nonlocal lastcpu,lastwall
  nowcpu=time.process_time();nowwall=time.monotonic();state['cpu']+=nowcpu-lastcpu;state['wall']+=nowwall-lastwall;lastcpu=nowcpu;lastwall=nowwall;state['totals']={k:fs.pack(x) for k,x in totals.items()};tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(state,sort_keys=True));os.replace(tmp,path)
 while state['cursor']<len(rows) and state['cpu']+time.process_time()-lastcpu<cpu_limit and state['wall']+time.monotonic()-lastwall<wall_limit:
  i=state['cursor'];row=rows[i];obj,data=c.read('/workspace/joint-stream-cache',row);reg,avg=store.state(i,len(obj['codes']));out={}
  for name,lib in [('original',old),('vector',new)]:
   start=time.process_time();out[name]=s.block(lib,obj,data,reg,avg,True);state['backend_cpu'][name]+=time.process_time()-start
  for field in FIELDS:
   error=max(abs(x-y) for x,y in zip(out['original'][field],out['vector'][field]));state['max_errors'][field]=max(state['max_errors'][field],error)
   if error>=1e-8:raise ValueError((i,field,error))
  weight=row['multiplicity']/22100
  for name in totals:
   data=out[name]['leaf']+out[name]['metrics']+out[name]['action_num']+out[name]['action_den']
   for j,x in enumerate(data):totals[name][j]+=weight*x
  state['cursor']+=1
  if state['cursor']%32==0:save();print(json.dumps({'orbits':state['cursor'],'cpu':state['cpu'],'wall':state['wall']}),flush=True)
 save();coverage=sum(r['multiplicity'] for r in rows[:state['cursor']])/22100;result={'identity':identity,'orbits':state['cursor'],'physical_coverage':coverage,'cpu_seconds':state['cpu'],'wall_seconds':state['wall'],'max_abs_errors':state['max_errors'],'backend_cpu':state['backend_cpu'],'full_population_pass':state['cursor']==1755,'normal_GTO':False,'real_game_error':'UNKNOWN'}
 if state['cursor']==1755:
  metrics={}
  for name,total in totals.items():
   br=s.collapse(total[:L]);metrics[name]={'root_nc':sum(br),'root_sb_ev':total[L]}
  result['root_metrics']=metrics;result['max_action_ev_difference']=max(abs(a/b-c/d) for a,b,c,d in zip(totals['original'][L+3:L+3+P],totals['original'][L+3+P:],totals['vector'][L+3:L+3+P],totals['vector'][L+3+P:]) if b>0 and d>0)
  assert abs(metrics['vector']['root_nc']-.9321071527220774)<1e-8 and result['max_action_ev_difference']<1e-8
 (root/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--completion',action='store_true');a=p.parse_args();run(a.root,1200 if a.completion else 900,1800 if a.completion else 1500)
