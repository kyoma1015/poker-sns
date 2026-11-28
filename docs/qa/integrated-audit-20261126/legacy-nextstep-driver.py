import sys,gzip,json,tempfile,hashlib
from pathlib import Path
from gto.qualification import integrated_study as old,integrated_solver as u,sparse_solver as s
from gto.qualification.native_mccfr import digest
old.load('/tmp/native-qualification');seed=int(sys.argv[1]);mode=sys.argv[2];im=old.module(next(Path('/tmp/integrated-v3' if mode=='old' else '/tmp/integrated-audit').glob('*.so')));m=s.load(next(Path('/tmp/sparse').glob('*.so')));w,o=s.warm(m,seed);q=u.Solver(im,w,o,seed+2100000,extra_support=[dict(round=0,history=[],actions=[18,19])],rows=500000)
p=old.ROOT/'support-preserved'/str(seed)/'last';meta=json.loads((p/'checkpoint.json').read_text());raw=gzip.decompress((p/'checkpoint.bin.gz').read_bytes());assert hashlib.sha256(raw).hexdigest()==meta['sha256']
for f,h in meta['identity']['sources'].items():
 x=Path(f)
 if x.name in ('integrated_native.cc','integrated_solver.py'):x=Path('docs/qa/integrated-audit-20261126/source-before')/x.name
 assert hashlib.sha256(x.read_bytes()).hexdigest()==h
with tempfile.TemporaryDirectory() as d:
 f=Path(d)/'cp';f.write_bytes(raw);q.core.restore(str(f),digest(meta['identity']))
r=q.step(10);assert r['complete'],r;q.core.save('/tmp/audit-next-'+str(seed)+'-'+mode+'.bin','same');print(seed,mode,r)
