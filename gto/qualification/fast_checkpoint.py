"""Lossless deterministic low-compression snapshots, atomically published."""
import gzip,json,os
from pathlib import Path

def save(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    payload=gzip.compress(json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode(),compresslevel=1,mtime=0)
    temp=path.with_name(path.name+'.pending')
    with temp.open('wb') as stream:
        stream.write(payload);stream.flush();os.fsync(stream.fileno())
    os.replace(temp,path)
    return len(payload)
