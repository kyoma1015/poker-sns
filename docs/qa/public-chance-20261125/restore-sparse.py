import gc,json,subprocess,tempfile
from pathlib import Path
from gto.qualification import sparse_solver as s
from gto.qualification.native_mccfr import digest
from gto.qualification.policy import sha
from gto.qualification.build import load
from gto.qualification.evaluate import atomic
root=Path('docs/qa/public-chance-20261125');root.mkdir(exist_ok=True)
m=s.load(next(Path('/tmp/sparse').glob('*.so')));rules,native=load('/tmp/native-qualification');records=[]
for seed in (17120101,17120102):
 p=Path('docs/qa/sparse-generalization-20261124/hu-final')/str(seed)/'compact/best';meta=json.loads((p/'checkpoint.json').read_text());identity=meta['identity']
 for path,expected in identity['sources'].items():assert sha(Path(path))==expected,path
 w,origin=s.warm(m,seed);q=s.Solver(m,w,origin,seed+1500000,sharing=True,extra_support=identity['extra_support'],rows=250000)
 with tempfile.TemporaryDirectory() as stage:
  raw=Path(stage)/'cp.bin'
  with raw.open('wb') as out:subprocess.run(['zstd','-d','-q','-c',str(p/'checkpoint.bin.zst')],stdout=out,check=True)
  assert sha(raw)==meta['sha256']
  q.core.restore(str(raw),digest(identity))
  r=m.Sparse(__import__('gto.native.training',fromlist=['NativeGame']).NativeGame([100,100]),dict(w,sharing=True,extra_support=identity['extra_support']),seed+1500000,False,True,250000,1000000)
  r.restore(str(raw),digest(identity));q.core.step(0.000001);r.step(0.000001)
  a=Path(stage)/'a.bin';b=Path(stage)/'b.bin';q.core.save(str(a),'migration-proof');r.save(str(b),'migration-proof');assert a.read_bytes()==b.read_bytes()
  records.append(dict(seed=seed,source_hashes_match=True,raw_sha256=meta['sha256'],old_binary=identity['binary_sha256'],new_binary=sha(Path(m.__file__)),same_binary=False,restored_real_R_A_RNG=True,new_build_next_batch_bit_exact=True,strict_old_binary_resume=False))
 del q,r,w;gc.collect()
atomic(root/'recovery.json',dict(records=records,base_head='af804c7a8173099fb737c2822fc872f8df6e737c',untracked_old_environment_recovered=False))
print(json.dumps(records))
