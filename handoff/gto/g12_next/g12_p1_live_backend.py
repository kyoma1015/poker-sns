"""Experimental SQLite live-training backend for G12 native Solver.
Rows are exact G12 binary row payloads; each iteration is an atomic transaction
covering changed rows, RNG, iteration, and sampled visit count.
"""
import hashlib
import sqlite3
from pathlib import Path

class LiveBackend:
    def __init__(self, path, *, cache_kib=1024):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.path,isolation_level=None)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('PRAGMA mmap_size=0')
        self.db.execute(f'PRAGMA cache_size=-{int(cache_kib)}')
        self.db.execute('CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY,v TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS rows(k BLOB PRIMARY KEY, data BLOB NOT NULL, digest BLOB NOT NULL) WITHOUT ROWID')
        self.active=False
        self.hits=0;self.misses=0;self.writes=0
    def initialize(self, fingerprint):
        row=self.db.execute("SELECT v FROM meta WHERE k='fingerprint'").fetchone()
        if row:
            if row[0]!=fingerprint:raise ValueError('solver contract mismatch')
            keys=dict(self.db.execute('SELECT k,v FROM meta'))
            if not all(k in keys for k in ('iteration','visits','rng')):
                if not any(k in keys for k in ('iteration','visits','rng')) and self.count()==0:
                    return None  # interrupted before first committed iteration
                raise ValueError('incomplete disk metadata')
            return int(keys['iteration']),int(keys['visits']),keys['rng']
        if self.db.execute('SELECT count(*) FROM rows').fetchone()[0]:raise ValueError('orphan rows without metadata')
        self.db.execute('INSERT INTO meta VALUES (?,?)',('fingerprint',fingerprint))
        return None
    def begin(self):
        if self.active:raise RuntimeError('nested transaction')
        self.db.execute('BEGIN IMMEDIATE');self.active=True
    def get(self,k):
        r=self.db.execute('SELECT data,digest FROM rows WHERE k=?',(bytes(k),)).fetchone()
        if r is None:self.misses+=1;return None
        self.hits+=1
        if hashlib.sha256(r[0]).digest()!=r[1]:raise ValueError('row corruption')
        return r[0]
    def commit(self,rows,rng,iteration,visits):
        if not self.active:raise RuntimeError('no active transaction')
        # Bind a bounded batch of row parameters instead of making one Python
        # sqlite3.execute call per infoset. The surrounding BEGIN IMMEDIATE /
        # COMMIT remains one atomic solver iteration (no intermediate commits).
        # The 256-row limit avoids materializing the whole changed-row set twice.
        def bindings():
            for k,v in rows:
                k=bytes(k);v=bytes(v)
                yield (k,v,hashlib.sha256(v).digest())
                self.writes+=1
        it=iter(bindings())
        while True:
            batch=list(__import__('itertools').islice(it,256))
            if not batch:break
            self.db.executemany('INSERT OR REPLACE INTO rows VALUES (?,?,?)',batch)
        for k,v in [('rng',rng),('iteration',str(iteration)),('visits',str(visits))]:
            self.db.execute('INSERT OR REPLACE INTO meta VALUES (?,?)',(k,v))
        self.db.execute('COMMIT');self.active=False
    def rollback(self):
        if self.active:self.db.execute('ROLLBACK');self.active=False
    def iter_keys(self):
        """Stream committed keys in the exact Native std::map byte ordering."""
        if self.active:raise RuntimeError('reads forbidden during uncommitted iteration')
        for (key,) in self.db.execute('SELECT k FROM rows ORDER BY k'):
            yield key

    def count(self):return self.db.execute('SELECT count(*) FROM rows').fetchone()[0]
    def close(self):
        self.rollback();self.db.close()

    def export_native_checkpoint(self, destination, contract, *, epsilon=0.6, alpha=0.1,
                                 full_support=True, compact=True, intern=True,
                                 baseline=True, wide=True):
        """Export a committed SQLite snapshot to native G12 checkpoint format.

        Explicit caller-supplied solver configuration must match the contract
        used at enable_disk_backend; load_binary validates it on re-import.
        """
        import os,struct
        if self.active:raise RuntimeError('cannot export uncommitted iteration')
        meta=dict(self.db.execute('SELECT k,v FROM meta'))
        if not all(k in meta for k in ('iteration','visits','rng','fingerprint')):
            raise ValueError('no committed solver state')
        def u(n):return struct.pack('<Q',int(n))
        def s(b):return u(len(b))+b
        def d(v):return struct.pack('<d',float(v))
        target=Path(destination);tmp=target.with_name(target.name+'.partial')
        try:
            self.db.execute('BEGIN')
            with open(tmp,'wb') as f:
                f.write(b'PIDG12S1');f.write(s(contract.encode()))
                for flag in (full_support,compact,intern,baseline,wide):f.write(u(flag))
                f.write(d(alpha));f.write(u(meta['iteration']));f.write(u(meta['visits']))
                f.write(d(epsilon));f.write(s(meta['rng'].encode()))
                count=self.count();f.write(u(count))
                for k,data,digest in self.db.execute('SELECT k,data,digest FROM rows ORDER BY k'):
                    if hashlib.sha256(data).digest()!=digest:raise ValueError('corrupt disk row')
                    f.write(s(k));f.write(data)
                f.flush();os.fsync(f.fileno())
            digest=hashlib.sha256()
            with open(tmp,'rb') as check:
                for part in iter(lambda:check.read(1<<20),b''):
                    digest.update(part)
            with open(tmp,'ab') as f:
                f.write(digest.digest());f.flush();os.fsync(f.fileno())
            self.db.execute('COMMIT')
            os.replace(tmp,target)
        except BaseException:
            if self.db.in_transaction:self.db.execute('ROLLBACK')
            if tmp.exists():tmp.unlink()
            raise
        return {'rows':count,'bytes':target.stat().st_size}
