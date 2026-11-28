"""Legal pure BR extraction. Policies, not invented CFR regret histories."""
import ctypes as C,hashlib,json,sqlite3,subprocess
from pathlib import Path
from gto.abstract import joint_stream as s,joint_stream_cache as cache,fullsupport as fs,model

def build(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);out=directory/'pure-br.so'
    subprocess.run(['c++','-std=c++17','-O3','-ffp-contract=off','-fno-tree-vectorize','-shared','-fPIC',str(Path(__file__).with_suffix('.cc')),'-o',str(out)],check=True)
    lib=C.CDLL(str(out.resolve()));fn=lib.extract_block;fn.argtypes=[C.c_int]*4+[model.IP]*10+[model.DP]*11+[model.IP];fn.restype=C.c_int
    def call(*args):
        choices=(C.c_int*args[2])();rc=fn(*args,choices);lib.choices=list(choices);lib.cf_mass=list(args[-1]);return rc
    lib.stream_block=call
    return lib

class Frozen:
    """Read-only snapshot; no WAL/state identity mutation on protected source."""
    board=s.Store.board;state=s.Store.state
    digest=s.Store.digest
    def __init__(self,path,rows):
        self.path=Path(path);self.rows=rows;self.pre=s.layout(1)[3]
        self.db=sqlite3.connect(self.path.resolve().as_uri()+'?mode=ro',uri=True);self.db.execute('BEGIN')
        expected=fs.digest({'source':s.source_identity(),'producer':cache.identity(),'population':rows,'nodes':s.tree()[0],'version':1})
        self.identity=expected
        if self.meta()['identity']!=expected or self.meta()['epoch'] or self.meta()['cursor'] or not self.get('baseline:ready'):raise ValueError('complete pinned frozen baseline required')
    def get(self,key):
        r=self.db.execute('select value from state where key=?',(key,)).fetchone();return None if r is None else r[0]
    def meta(self):return json.loads(self.get('meta'))
    def numeric_digest(self):return fs.digest([(k,hashlib.sha256(v).hexdigest()) for k,v in self.db.execute("select key,value from state where key!='meta' and key not like 'eval:%' order by key")])
    def close(self):self.db.close()

def collapse_policy(leaf,nodes=None):
    nodes=model.tree() if nodes is None else nodes;B=len(nodes)
    if len(leaf)!=2*B*169:raise ValueError('full leaf shape')
    values=[];choices={}
    for owner in (0,1):
        v=[None]*B
        for k in range(B-1,-1,-1):
            n=nodes[k]
            if n['actor']<0:v[k]=leaf[(owner*B+k)*169:(owner*B+k+1)*169]
            elif n['actor']==owner:
                selected=[max(range(len(n['children'])),key=lambda a:v[n['children'][a]][h]) for h in range(169)]
                choices[k]=selected;v[k]=[v[n['children'][selected[h]]][h] for h in range(169)]
            else:v[k]=[sum(v[c][h] for c in n['children']) for h in range(169)]
        values.append(sum(v[0]))
    return choices,values

def prefix_bytes(leaf):
    choices,values=collapse_policy(leaf);ns,mapping,_=s.tree();reverse={v:k for k,v in mapping.items()};out=[]
    for start,T,n,k in s.layout(1)[2]:
        if start<s.layout(1)[3]:out.extend(choices[reverse[k]])
    return bytes(out),values

def post_bytes(choices,T):
    out=[]
    for start,types,n,k in s.layout(T)[2]:
        if start>=s.layout(T)[3]:
            for typ in range(types):
                a=choices[start+typ*n]
                if not 0<=a<n:raise ValueError('legal pure OWN-info choice required')
                out.append(a)
    return bytes(out)

def pure_policy(prefix,post,T):
    ns,_,rows,P,S,_=s.layout(T);out=[0.]*S;prepos=postpos=0
    for start,types,n,k in rows:
        for typ in range(types):
            if start<P:
                if prepos>=len(prefix):raise ValueError('prefix shape')
                a=prefix[prepos];prepos+=1
            else:
                if postpos>=len(post):raise ValueError('post shape')
                a=post[postpos];postpos+=1
            if not 0<=a<n:raise ValueError('illegal pure action')
            out[start+typ*n+a]=1.
    if prepos!=len(prefix) or postpos!=len(post):raise ValueError('extra pure actions')
    return out

def hybrid(baseline,pure,T,owner):
    out=baseline.copy();ns,_,rows,_,_,_=s.layout(T)
    for start,types,n,k in rows:
        if ns[k]['actor']==owner:out[start:start+types*n]=pure[start:start+types*n]
    return out
