"""Emit/check ONLY the existing HU50 research tree; not a formal sizing registry."""
import argparse,hashlib,json
from pathlib import Path
from gto.abstract import model

def render():
    return json.dumps({'scope':'existing_research_only_not_formal_spec','model_source_sha256':hashlib.sha256(Path(model.__file__).read_bytes()).hexdigest(),'nodes':model.tree()},sort_keys=True,indent=2)+'\n'
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();path=Path('gto/release/researchLayout.json')
    if a.check:
        assert path.read_text()==render();print('PASS unchanged research tree layout, not formal sizing')
    else:
        with path.open('x') as f:f.write(render())
