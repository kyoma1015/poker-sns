"""Keep historical numerical evidence immutable while explicitly auditing UI evolution."""
import hashlib,json,subprocess
from pathlib import Path

HISTORICAL_HEAD='25142ce7a17f6713787c5e8365ec50073f8ef23b'
UI_EVOLUTION={'src/GtoPreflop.tsx','src/gto/rangeCatalog.ts'}

def verify_historical_sources(old_manifest,current_sources):
    changed=[]
    for name,expected in old_manifest['source_sha256'].items():
        actual=hashlib.sha256(Path(name).read_bytes()).hexdigest()
        if actual==expected:continue
        if name not in UI_EVOLUTION:raise ValueError('historical numerical source changed: '+name)
        original=subprocess.check_output(['git','show',HISTORICAL_HEAD+':'+name])
        if hashlib.sha256(original).hexdigest()!=expected:raise ValueError('historical source identity mismatch: '+name)
        if current_sources.get(name)!=actual:raise ValueError('current UI not pinned/tested in release evidence: '+name)
        changed.append(name)
    return changed

def verify():
    root=Path('docs/qa/preflop-release-20261116');manifest=json.loads((root/'manifest.json').read_text())
    for group,base in (('source_sha256',Path('.')),('evidence_sha256',root)):
        for name,h in manifest[group].items():
            if hashlib.sha256((base/name).read_bytes()).hexdigest()!=h:raise ValueError('release identity mismatch: '+name)
    old=json.loads(Path('docs/qa/matched-history-20261116/manifest.json').read_text())
    evolved=verify_historical_sources(old,manifest['source_sha256'])
    print('PASS release hashes; historical numerical sources retained; separately verified UI evolution:',evolved)

if __name__=='__main__':verify()
