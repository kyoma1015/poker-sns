"""Linux-only fixture subreaper; never installed or applied to the controller."""
import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import code_worker as worker


def alive(pid):
    try:return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
    except FileNotFoundError:return False


def reap(pid):
    deadline=time.monotonic()+1
    while time.monotonic()<deadline:
        try:
            got,status=os.waitpid(pid,os.WNOHANG)
        except ChildProcessError:return None
        if got:return os.WTERMSIG(status) if os.WIFSIGNALED(status) else 0
        time.sleep(.01)
    return None


def role(name,path,escaped):
    signal.signal(signal.SIGTERM,signal.SIG_IGN)
    if name=='grand':
        print('READY',flush=True)
    else:
        child=subprocess.Popen([sys.executable,'-B',__file__,'--role',
                                'grand' if name=='child' else 'child',str(path),str(int(escaped))],
                               stdout=subprocess.PIPE,text=True,
                               start_new_session=escaped and name=='child')
        line=child.stdout.readline()
        if name=='child':
            assert line.strip()=='READY'
            print(json.dumps({'child':os.getpid(),'grand':child.pid}),flush=True)
        else:
            ids=json.loads(line);ids['leader']=os.getpid()
            path.write_text(json.dumps(ids))
    time.sleep(30)


def probe(path,escaped):
    path=path.resolve()
    if (not path.is_relative_to(Path(tempfile.gettempdir()).resolve())
            or not path.parent.name.startswith('owned-tree-qa-')):
        raise ValueError('owned temporary probe path required')
    if ctypes.CDLL(None).prctl(36,1,0,0,0)!=0:
        raise RuntimeError('fixture subreaper unavailable')
    ids={}
    try:
        started=time.monotonic()
        try:
            worker.command([sys.executable,'-B',__file__,'--role','parent',str(path),str(int(escaped))],path.parent,timeout=.4)
            raise AssertionError('fixture must timeout')
        except subprocess.TimeoutExpired as error:
            unknown=getattr(error,'worker_liveness_unknown',False)
        ids=json.loads(path.read_text())
        result={'ids':ids,'command_seconds':time.monotonic()-started,
                'escaped_survived':alive(ids['grand']),'worker_liveness_unknown':unknown,
                'child_reaped_signal':reap(ids['child'])}
        if escaped:
            result['automatic_full_tree_liveness']='UNKNOWN'
            os.kill(ids['grand'],signal.SIGKILL)
        result['grand_reaped_signal']=reap(ids['grand'])
        print(json.dumps(result),flush=True)
    finally:
        if not ids and path.exists():ids=json.loads(path.read_text())
        for pid in ids.values():
            try:os.kill(pid,signal.SIGKILL)
            except ProcessLookupError:pass
        for pid in ids.values():reap(pid)


if __name__=='__main__':
    if sys.argv[1]=='--role':role(sys.argv[2],Path(sys.argv[3]),sys.argv[4]=='1')
    else:probe(Path(sys.argv[1]),sys.argv[2]=='1')
