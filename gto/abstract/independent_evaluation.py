"""Independent whole-policy observations retain all public-flop correlations."""
import ctypes as C,json,math
from gto.abstract import fullsupport as fs,call_reach as cr,model
from gto.abstract.model import doubles

def weights(policy,names):
 probability=model.chance(model.classes())[1];rows=cr.leaf_ledger(policy);fold=math.fsum(x['probability']*x['fold_sb_payoff_bb'] for x in rows if not x['matched']);out={}
 for row in rows:
  if not row['matched']:continue
  r=cr.extract(policy,row['history'],'leaf');out[row['leaf']]=[probability[i*169+j]*r['seat_reach'][0][i]*r['seat_reach'][1][j] for i in range(169) for j in range(169)]
 return out,fold

def mix(a,b):
 n=169;out=list(a)
 for k,node in enumerate(model.tree()):
  if node['actor']==1:out[k*3*n:(k+1)*3*n]=b[k*3*n:(k+1)*3*n]
 return out

def measure(native,policies,frozen,names,bounds,draws,control,cache,identity,failure=.005):
 w0,f0=weights(frozen,names);records=[];vectors=[];constants=[];ranges=[]
 for variant,pi in policies.items():
  w1,f1=weights(pi,names);ws,fsb=weights(mix(pi,frozen),names);wb,fbb=weights(mix(frozen,pi),names)
  configs=[('learned_profile',w1,f1),('frozen_profile',w0,f0),('candidate_SB_gain_vs_frozen',{k:[x-y for x,y in zip(ws[k],w0[k])] for k in w0},fsb-f0),('candidate_BB_gain_vs_frozen',{k:[x-y for x,y in zip(w0[k],wb[k])] for k in w0},f0-fbb)]
  for label,w,constant in configs:
   vector=[x if name==variant else 0. for name,leaf in names for x in w[leaf]];bound_range=math.fsum(abs(x)*2*bounds[p]*fs.WMAX for p in range(len(names)) for x in vector[p*fs.S:(p+1)*fs.S]);vectors.extend(vector);constants.append(constant);ranges.append(bound_range);records.append({'variant':variant,'metric':label})
 count=len(records);means=(C.c_double*count)();m2=(C.c_double*count)();wc=doubles(vectors);cc=doubles(constants);pc=doubles(control)
 for i,flop in enumerate(draws):
  path=cache/(fs.digest({'identity':identity,'flop':flop})+'.json');data=json.loads(path.read_text());y=fs.unpack(data['payoff']);mass=fs.unpack(data['mass'])
  if native.scalar_update(len(names),count,i+1,doubles(y),doubles(mass),pc,wc,cc,means,m2):raise ValueError('whole-policy independent estimate')
 out=[];log=math.log(4/(failure/count));n=len(draws)
 for i,row in enumerate(records):
  var=max(0.,m2[i]/(n-1));radius=math.sqrt(2*var*log/n)+7*ranges[i]*log/(3*(n-1))+1e-7;out.append({**row,'estimate_bb':means[i],'interval_bb':[means[i]-radius,means[i]+radius],'radius_bb':radius,'independent_samples':n,'variance_of_whole_correlated_observation':var,'bounded_observation_range_bb':ranges[i]})
 return {'rows':out,'confidence_family':1-failure,'candidate_selection_performed':False,'scope':'fixed independent preflop candidates against frozen preflop strategies in SAME learned continuation model;not external GTO improvement'}
