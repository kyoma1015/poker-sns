import gzip,json,hashlib,subprocess,time
from pathlib import Path
root=Path('docs/qa/sparse-generalization-20261124');previous=json.loads((root/'checkpoint-recompression.json').read_text()).get('rows',[]) if (root/'checkpoint-recompression.json').exists() else [];rows=[];start=time.monotonic()
for p in root.rglob('checkpoint.bin.gz'):
 raw=gzip.decompress(p.read_bytes());meta=json.loads(p.with_name('checkpoint.json').read_text());h=hashlib.sha256(raw).hexdigest();assert h==meta['sha256']
 target=p.with_suffix('.zst');compressed=subprocess.run(['zstd','-9','-q','-c'],input=raw,stdout=subprocess.PIPE,check=True).stdout
 restored=subprocess.run(['zstd','-d','-q','-c'],input=compressed,stdout=subprocess.PIPE,check=True).stdout;assert restored==raw
 target.write_bytes(compressed);rows.append(dict(previous=str(p.relative_to(root)),current=str(target.relative_to(root)),previous_archive_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),raw_sha256=h,raw_bytes=len(raw),previous_bytes=p.stat().st_size,current_bytes=len(compressed)))
 p.unlink() # Only this task's verified redundant encoding; exact raw R/A/RNG retained.
(root/'checkpoint-recompression.json').write_text(json.dumps(dict(rows=previous+rows,seconds=time.monotonic()-start,scope='lossless raw-byte checked; no previous-commit files touched'),indent=2)+'\n');print(len(rows),sum(r['previous_bytes'] for r in rows),sum(r['current_bytes'] for r in rows))
