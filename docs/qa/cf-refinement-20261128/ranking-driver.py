import json,gc,time,resource,hashlib
from pathlib import Path
from gto.qualification import public_stream_study as store,stream_sampling as ss,stream_chance as sc,cf_refine as cf,stream_measure as sm
for seed in (17120101,17120102):
 start=time.monotonic();q,meta,rng=store.restore(f'docs/qa/public-stream-final-20261127/{seed}/t64');snapshot=ss.replace_bank(q,sc.catalog(q.lib,17160101+seed),average_snapshot=True);del q;gc.collect();scores=cf.scores(snapshot);rows=scores[:8];before=sm.refinement_envelope(snapshot)
 folder=Path(f'docs/qa/cf-refinement-20261128/{seed}');folder.mkdir();(folder/'selection-rank.json').write_text(json.dumps(dict(rows=scores,chosen=rows,before=before,seconds=time.monotonic()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,formal_pass=0),indent=2));print(seed,rows,before,flush=True);del snapshot;gc.collect()
