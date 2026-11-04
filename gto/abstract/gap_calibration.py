"""Public-stage/own-seat arm calibration; no actual opponent private inputs."""
import math
from gto.abstract.continuation_learning import FrozenContinuation
from gto.abstract import gap_models as gm


def fit(rows):
 sums={}
 for row in rows:
  for k,t in row['reference']['targets'].items():
   if t['ev'] is None:continue
   pred=row['predictions'][k];w=t['mass']
   for a,(x,y) in enumerate(zip(pred,t['ev'])):
    key=(row['stage'],k[0],a);v=sums.setdefault(key,[0.]*5)
    for i,z in enumerate((w,w*x,w*y,w*x*x,w*x*y)):v[i]+=z
 coefficients=[]
 for (stage,actor,arm),(w,wx,wy,wxx,wxy) in sorted(sums.items()):
  x,y=wx/w,wy/w;variance=wxx/w-x*x;slope=max(0.,min(2.,(wxy/w-x*y)/variance)) if variance>=1e-12 else 1.
  coefficients.append({'stage':stage,'actor':actor,'arm':arm,'bias':y-x,'affine_slope':slope,'affine_intercept':y-slope*x,'weight':w})
 return coefficients


def predict(raw,k,stage,method,coefficients):
 if method=='raw':return tuple(raw)
 table={(r['stage'],r['actor'],r['arm']):r for r in coefficients};out=[]
 for a,x in enumerate(raw):
  c=table[(stage,k[0],a)];out.append(x+c['bias'] if method=='bias' else c['affine_slope']*x+c['affine_intercept'])
 return tuple(out)


def errors(g,ref,predictions,stage,method,coefficients):
 mae=[0.]*4;maximum=[0.]*4;loss=0.;table={}
 for k,t in ref['targets'].items():
  values=predict(predictions[k],k,stage,method,coefficients);best=max(values);ties=[a for a,v in enumerate(values) if best-v<=1e-12];p=tuple(float(a in ties)/len(ties) for a in range(4));table[k]=p
  if t['ev'] is None:continue
  for a in range(4):
   e=abs(values[a]-t['ev'][a]);mae[a]+=t['mass']*e/2;maximum[a]=max(maximum[a],e)
  loss+=t['mass']*(max(t['ev'])-math.fsum(v*w for v,w in zip(t['ev'],p)))
 profile=gm.evaluate(g,FrozenContinuation(table))
 return {'action_mae_bb':mae,'action_max_error_bb':maximum,'mean_action_mae_bb':math.fsum(mae)/4,'maximum_action_error_bb':max(maximum),'one_sided_greedy_regret_loss_bb':loss,'simultaneous_greedy_profile_nashconv_bb':profile['restricted_nashconv_bb'],'simultaneous_greedy_profile_ev_bb':profile['profile_hero_ev_bb'],'reference':'independent concrete-pair cash ledger against frozen probability controller; not external GTO'}


def summary(rows):
 def one(xs):return {'contexts':len(xs),'mean_action_mae_bb':math.fsum(x['errors']['mean_action_mae_bb'] for x in xs)/len(xs),'maximum_action_error_bb':max(x['errors']['maximum_action_error_bb'] for x in xs),'action_mae_bb':[math.fsum(x['errors']['action_mae_bb'][a] for x in xs)/len(xs) for a in range(4)],'action_max_error_bb':[max(x['errors']['action_max_error_bb'][a] for x in xs) for a in range(4)],'mean_one_sided_greedy_regret_loss_bb':math.fsum(x['errors']['one_sided_greedy_regret_loss_bb'] for x in xs)/len(xs),'mean_simultaneous_greedy_nashconv_bb':math.fsum(x['errors']['simultaneous_greedy_profile_nashconv_bb'] for x in xs)/len(xs)}
 return {'overall':one(rows),'by_stage':{s:one([r for r in rows if r['stage']==s]) for s in ('vs_3bet','vs_4bet')}}


def choose(candidates):
 raw=next(c['summary'] for c in candidates if c['method']=='raw');eligible=[]
 for c in candidates:
  v=c['summary'];ok=v['overall']['maximum_action_error_bb']<=raw['overall']['maximum_action_error_bb']+1e-9 and all(v['by_stage'][s][m]<=raw['by_stage'][s][m]+1e-9 for s in ('vs_3bet','vs_4bet') for m in ('mean_action_mae_bb','mean_one_sided_greedy_regret_loss_bb'))
  if ok:eligible.append(c)
 return min(eligible,key=lambda c:c['summary']['overall']['mean_action_mae_bb'])['method']
