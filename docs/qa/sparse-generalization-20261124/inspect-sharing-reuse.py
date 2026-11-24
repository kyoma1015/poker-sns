import json,gc
from pathlib import Path
from gto.qualification import sparse_solver as s,sparse_study as st
from gto.qualification.build import load
from gto.native.training import NativeGame
from gto.qualification.evaluate import atomic
root=Path('docs/qa/sparse-generalization-20261124');rules,native=load('/tmp/poker-public-response-build');module=s.load('/tmp/sparse-sharing-final-build/_sparse_qualification.cpython-312-x86_64-linux-gnu.so')
(root/'final-evaluation-driver.py').write_bytes(Path(st.__file__).read_bytes())
for seed in (17120101,17120102):
 folder=root/'hu-final'/str(seed)/'compact';meta=json.loads((folder/'pilot.json').read_text());w,origin=s.warm(module,seed);q=s.Solver(module,w,origin,seed+1500000,sharing=True,extra_support=meta['extra_support'],rows=250000);s.bootstrap_preflop(q,Path('docs/qa/legal-size-20261124/hu-final')/str(seed)/'best',rules);st.archive_restore(q,folder/'best');del w;gc.collect()
 counts={r:dict(queries=0,strategic=0,average_trained=0,strategic_average_trained=0,strategic_regret_trained=0,strategic_both=0) for r in range(4)}
 class Audit:
  def row(self,o,average=False):
   r=q.core.query(o.own,o.board,o.actor,o.round,o.history,o.actions,o.live,o.street,o.remaining,o.price,True);c=counts[o.round];active=len(o.actions)>1;c['queries']+=1;c['strategic']+=active;c['average_trained']+=r['averages']>0;c['strategic_average_trained']+=active and r['averages']>0;c['strategic_regret_trained']+=active and r['visits']>0;c['strategic_both']+=active and r['averages']>0 and r['visits']>0;return r['probabilities']
 audit=Audit()
 for deck,tape in st.samples(17129501,8192):st.rb_value(audit,native,NativeGame([100,100]),deck,tape,module)
 atomic(root/'final'/str(seed)/'compact'/'reuse-decomposition.json',dict(policy_digest=q.policy_digest,final_seed=17129501,worlds=8192,counts=counts,scope='posthoc decomposition of same frozen final paths, no selection or strategy changes'))
 del q;gc.collect()
