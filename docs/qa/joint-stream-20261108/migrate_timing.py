"""Back up completed checkpoints; approve ONLY the reporting-variable rename.

No regret, average, payoff, reach, chance or evaluation accumulator is changed.
Run with PYTHONPATH set to the checkout. Requires the recorded9e865 source object.
"""
import hashlib,json,sqlite3,subprocess
from pathlib import Path
from gto.abstract import joint_stream as s,joint_stream_cache as c,fullsupport as fs

BASE='9e865e5668d001e080714ca3258e5a71b8e8a947'
OLD_BLOCK='''    for start,types,n,k in rows:
        if start<P:
            for t in range(types):bound+=max(0.,*prefix[start+t*n:start+(t+1)*n])'''
NEW_BLOCK='''    for row_start,types,n,k in rows:
        if row_start<P:
            for t in range(types):bound+=max(0.,*prefix[row_start+t*n:row_start+(t+1)*n])'''

def numeric_digest(db):
    return fs.digest([(k,hashlib.sha256(v).hexdigest()) for k,v in db.execute('SELECT key,value FROM state ORDER BY key') if k!='meta' and not k.startswith('migration:')])

def transition():
    old=subprocess.check_output(['git','show',BASE+':gto/abstract/joint_stream.py']).decode();current=Path(s.__file__).read_text()
    if old.count(OLD_BLOCK)!=1 or old.replace(OLD_BLOCK,NEW_BLOCK)!=current:raise ValueError('not the approved telemetry-only patch')
    old_source={**s.source_identity(),'joint_stream.py':hashlib.sha256(old.encode()).hexdigest()}
    common={'producer':c.identity(),'population':c.population(),'nodes':s.tree()[0],'version':1}
    old_id=fs.digest({**common,'source':old_source});new_id=fs.digest({**common,'source':s.source_identity()})
    return old_source,old_id,new_id

def run():
    old_source,old_id,new_id=transition()
    backup=Path('/workspace/joint-stream-before-timing');backup.mkdir(exist_ok=True)
    sources={'uniform4':Path('/workspace/joint-stream-run/learned.sqlite'),'frozen':Path('/workspace/joint-stream-run/frozen.sqlite'),'warm2':Path('/workspace/joint-stream-warm/learned.sqlite')};receipts=[]
    if sum(p.stat().st_size for p in sources.values())*2+sum(p.stat().st_size for p in Path('/workspace/joint-stream-cache').glob('*.json'))>12*1024**3:raise ValueError('backup/checkpoint12GiB budget')
    for name,path in sources.items():
        db=sqlite3.connect(path);meta=json.loads(db.execute("SELECT value FROM state WHERE key='meta'").fetchone()[0]);target=backup/(name+'.sqlite')
        if meta['identity']==new_id:
            if not target.exists():raise ValueError('migrated checkpoint missing original backup')
            prior=db.execute("SELECT value FROM state WHERE key='migration:timing-fix'").fetchone()
            if prior is None:raise ValueError('missing migration journal')
            receipt=json.loads(prior[0])['receipt'];digest=numeric_digest(db)
            copy=sqlite3.connect('file:'+str(target)+'?mode=ro',uri=True)
            if digest!=receipt['numeric_digest_before'] or numeric_digest(copy)!=digest:raise ValueError('checkpoint advanced since this migration;do not overwrite history')
            copy.close();receipt.update(numeric_digest_after=digest,numeric_state_unchanged=True,resumed=True);receipts.append(receipt)
            db.close();continue
        if meta['identity']!=old_id or meta['cursor']!=0:raise ValueError('completed expected source checkpoint required')
        before=numeric_digest(db)
        if not target.exists():
            copy=sqlite3.connect(target);db.backup(copy);copy.close()
        copy=sqlite3.connect('file:'+str(target)+'?mode=ro',uri=True)
        if numeric_digest(copy)!=before or json.loads(copy.execute("SELECT value FROM state WHERE key='meta'").fetchone()[0])['identity']!=old_id:raise ValueError('original backup mismatch')
        copy.close();new_meta={**meta,'identity':new_id}
        receipt={'name':name,'old_identity':old_id,'new_identity':new_id,'numeric_digest_before':before,'original_backup':str(target),'epoch':meta['epoch']}
        with db:
            db.execute('INSERT INTO state VALUES (?,?)',('migration:timing-fix',json.dumps({'old_meta':meta,'receipt':receipt}).encode()))
            db.execute('UPDATE state SET value=? WHERE key=?',(json.dumps(new_meta).encode(),'meta'))
        after=numeric_digest(db)
        if after!=before:raise ValueError('numeric state changed')
        receipt.update(numeric_digest_after=after,numeric_state_unchanged=True);receipts.append(receipt);db.close()
    out={'base':BASE,'approved_change':'rename reporting row offset; no numerical update changes','historical_source_identity':old_source,'current_source_identity':s.source_identity(),'old_checkpoint_identity':old_id,'new_checkpoint_identity':new_id,'receipts':receipts}
    Path('/workspace/joint-stream-timing-migration.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out))

if __name__=='__main__':
    import sys
    if '--verify-source-only' in sys.argv:
        old_source,old_id,new_id=transition();print(json.dumps({'approved_telemetry_only':True,'old_identity':old_id,'new_identity':new_id}))
    else:run()
