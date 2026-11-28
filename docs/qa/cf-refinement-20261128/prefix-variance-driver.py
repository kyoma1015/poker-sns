import json,gzip,time,random
from pathlib import Path
import numpy as np
from gto.qualification.stream_multiplayer import Stratified
from gto.qualification.prefix_sampling import Prefix
from gto.qualification.multiplayer_joint import expanded_decks,Joint,path_oracle
from gto.qualification.build import load
from gto.native.training import NativeGame
_,native=load('/tmp/native-qualification');game=NativeGame([24,22,20]);decks=expanded_decks(3);joint=Joint(native,game,decks,[.25]*4,max_nodes=5000,action_scope='preflop');records=[]
for seed in (17150201,17150202):
 raw=json.loads(gzip.decompress(Path(f'docs/qa/stream-subgame-20261127/multiplayer/3max-{seed}-iid.json.gz').read_bytes()));data=raw['A'];pi={k:np.array(v)/sum(v) if sum(v)>0 else np.ones(len(v))/len(v) for k,v in data.items()};expected=path_oracle(joint,{k:pi.get(k,np.ones(len(a))/len(a)) for k,a in joint.actions.items()})['grad'];keys=sorted(expected);exact=np.concatenate([expected[k] for k in keys])
 for mode,cls in [('chance_only',Stratified),('root_quantiles',Prefix)]:
  q=cls(native,game,decks=decks,weights=[.25]*4,seed=seed,chance_batch=4,average_mode='lazy',max_nodes=20000,max_seconds=10);samples=[];tick=time.process_time()
  for i in range(32):
   q._draw();g={}
   for owner in range(3):
    part=q.collect(owner,decks[0],random.Random(17161201+owner+37*i),pi)
    for k,v in part['grad'].items():g[k]=g.get(k,np.zeros(len(v)))+v
   samples.append(np.concatenate([g.get(k,np.zeros(len(expected[k]))) for k in keys]))
  arr=np.array(samples);records.append(dict(seed=seed,mode=mode,variance_trace=float(arr.var(axis=0,ddof=1).sum()),mean_squared_error_to_exact_oracle=float(np.square(arr.mean(axis=0)-exact).sum()),CPU_seconds=time.process_time()-tick,trials=32,formal_pass=0));print(records[-1],flush=True)
Path('docs/qa/cf-refinement-20261128/multiplayer-variance.json').write_text(json.dumps(dict(records=records,scope='fixed-policy raw-gradient pilot; no strategy quality or Nash claim'),indent=2)+'\n')
