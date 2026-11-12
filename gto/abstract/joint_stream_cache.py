"""Versioned, unweighted fine-private moments for every registered suit orbit."""
import argparse,ctypes as C,json,math,time
from pathlib import Path
from gto.abstract import model,fullsupport as fs,call_study as cs,suit_exact as old

def identity():
    from gto.abstract import flop_exact,continuation_game,continuation_learning,flop_conditional
    paths=[Path(__file__),Path(model.__file__),Path(fs.__file__),Path(flop_exact.__file__),Path(flop_exact.__file__).with_name('flop_exact_matrix.cc'),Path(continuation_game.__file__).with_suffix('.cc'),Path(continuation_learning.__file__),Path(flop_conditional.__file__)]
    import hashlib
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def population():
    rows=json.loads(old.DESIGN.read_text())['orbits']
    if len(rows)!=1755 or sum(r['multiplicity'] for r in rows)!=22100:raise ValueError('complete pinned population required')
    return rows

def filename(cache,row):return Path(cache)/(fs.digest({'row':row,'producer':identity()})+'.json')

def read(cache,row):
    obj=json.loads(filename(cache,row).read_text())
    if obj['producer']!=identity() or obj['row']!=row:raise ValueError('cache identity')
    values=fs.unpack(obj['moments']);n=len(obj['codes'])
    if len(values)!=2*n*n or obj['codes']!=sorted(set(obj['codes'])) or any(not 0<=x<1352 for x in obj['codes']):raise ValueError('private moment shape')
    if not math.isclose(math.fsum(values[::2]),1,abs_tol=1e-10) or any(not math.isfinite(x) or x<0 for x in values):raise ValueError('joint chance normalization')
    if max(abs(values[(i*n+j)*2+1]+values[(j*n+i)*2+1]-values[(i*n+j)*2]) for i in range(n) for j in range(n))>1e-10:raise ValueError('showdown conservation')
    return obj,values

def generate(build,cache,parity,*,seconds=3600,limit=1755):
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True);env=None;start=time.monotonic();done=0
    for i,row in enumerate(population()):
        if i%2!=parity:continue
        if time.monotonic()-start>=seconds or done>=limit:break
        if sum(p.stat().st_size for p in cache.glob('*.json'))>12*1024**3:raise ValueError('12GiB disk budget reached')
        if filename(cache,row).exists():read(cache,row);continue
        if env is None:env=cs.setup(Path(build))
        m=cs.exact.matrix(env[0],row['representative']);flags=fs.groups(m);signals=[c*8+g for c,g in zip(m['labels'],flags)];codes=sorted(set(signals));lookup={x:i for i,x in enumerate(codes)};ids=[lookup[x] for x in signals];n=len(codes);out=(C.c_double*(2*n*n))()
        if env[1].type_aggregate(m['n'],n,n,m['cards'],model.ints(m['labels']),model.ints(ids),model.ints(ids),m['win'],m['tie'],model.doubles([1.]*169),model.doubles([1.]*169),out):raise ValueError('unweighted moment kernel')
        packet=fs.pack(out);legacy=Path('/workspace/joint-reach-cache')/('joint-'+fs.digest(row)+'.json');reused=False
        if legacy.exists():
            prior=json.loads(legacy.read_text())
            if prior['codes']!=codes or prior['moments']['sha256']!=packet['sha256']:raise ValueError('legacy cache differs from fresh independent moments')
            packet=prior['moments'];reused=True
        obj={'producer':identity(),'row':row,'codes':codes,'moments':packet,'legacy_verified_and_reused':reused}
        target=filename(cache,row);temp=target.with_suffix('.tmp'+str(parity));temp.write_text(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n');temp.replace(target);done+=1
        if done%16==0:print(json.dumps({'parity':parity,'index':i,'generated':done,'seconds':time.monotonic()-start}),flush=True)
    return {'parity':parity,'new_blocks':done,'elapsed_seconds':time.monotonic()-start,'population':1755,'cache_files':len(list(cache.glob('*.json')))}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--cache',type=Path,required=True);p.add_argument('--parity',type=int,choices=(0,1),required=True);p.add_argument('--seconds',type=int,default=3600);a=p.parse_args();print(json.dumps(generate(a.build,a.cache,a.parity,seconds=a.seconds)),flush=True)
