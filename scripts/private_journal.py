"""Private append-only local records, requiring an externally pinned head.

Not WORM storage: a writer can rewrite the entire chain. Keep the expected head
outside this directory. Pending crash files are retained, never replayed. No host
connection, lease mutation, receipt interpretation or logging occurs here.
"""
import fcntl
import hashlib
import json
import math
import time
import os
from pathlib import Path
import stat
import uuid


def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')


class PrivateJournal:
    def __init__(self,path):
        self.path=Path(path)
        self.path.mkdir(mode=0o700,parents=False,exist_ok=True)
        info=self.path.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_mode&0o077 or info.st_uid!=os.getuid():
            raise ValueError('private owned non-symlink journal directory required')

    def _directory(self):
        fd=os.open(self.path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        info=os.fstat(fd)
        if info.st_mode&0o077 or info.st_uid!=os.getuid():
            os.close(fd)
            raise ValueError('private owned directory required')
        return fd

    def _read(self,fd,expected_head):
        names=sorted(n for n in os.listdir(fd) if not n.startswith('.pending-') and n!='.lock')
        previous=None;values=[]
        for index,name in enumerate(names):
            if name!=f'{index:016d}.json':raise ValueError('journal sequence missing or reordered')
            recordfd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd)
            with os.fdopen(recordfd,'rb') as inp:
                info=os.fstat(inp.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_mode&0o077 or info.st_uid!=os.getuid():raise ValueError('private regular record required')
                raw=inp.read()
            try:
                record=json.loads(raw)
                if set(record)!={'index','previous','payload','digest'}:raise ValueError('invalid record fields')
                body={k:record[k] for k in ('index','previous','payload')}
                digest=hashlib.sha256(_canonical(body)).hexdigest()
                if record['index']!=index or type(record['index']) is not int or record['previous']!=previous or record['digest']!=digest or raw!=_canonical(record):raise ValueError('invalid journal chain')
            except (UnicodeError,TypeError,KeyError,json.JSONDecodeError) as error:raise ValueError('invalid journal record') from error
            previous=digest;values.append(record['payload'])
        if previous!=expected_head:raise ValueError('external pinned head mismatch')
        return values

    def read(self,*,expected_head):
        fd=self._directory()
        try:return self._read(fd,expected_head)
        finally:os.close(fd)

    def append(self,payload,*,expected_head,lock_timeout=1.0):
        # Serialize first; reject NaN, unsupported types without leaving artifacts.
        _canonical(payload)
        if type(lock_timeout) not in (int,float) or not math.isfinite(lock_timeout) or not 0<=lock_timeout<=5:
            raise ValueError('lock timeout must be finite within zero to five seconds')
        fd=self._directory();lock=None;pending=None
        try:
            lock=os.open('.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600,dir_fd=fd)
            info=os.fstat(lock)
            if not stat.S_ISREG(info.st_mode) or info.st_mode&0o077 or info.st_uid!=os.getuid():raise ValueError('private journal lock required')
            deadline=time.monotonic()+lock_timeout
            while True:
                try:
                    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    remaining=deadline-time.monotonic()
                    if remaining<=0:raise TimeoutError('private journal lock deadline exceeded')
                    time.sleep(min(0.01,remaining))
            values=self._read(fd,expected_head)
            body={'index':len(values),'previous':expected_head,'payload':payload}
            digest=hashlib.sha256(_canonical(body)).hexdigest();raw=_canonical(dict(body,digest=digest))
            pending='.pending-'+uuid.uuid4().hex
            outfd=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
            with os.fdopen(outfd,'wb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
            # link is exclusive and cannot replace any existing committed record.
            os.link(pending,f'{len(values):016d}.json',src_dir_fd=fd,dst_dir_fd=fd,follow_symlinks=False)
            os.fsync(fd)
            os.unlink(pending,dir_fd=fd);pending=None;os.fsync(fd)
            return digest
        finally:
            if lock is not None:os.close(lock)
            os.close(fd)
