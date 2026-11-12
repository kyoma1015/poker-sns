"""Independent arithmetic checks on measured BR realization certificates.

This checks committed measurements; it does NOT replay population kernels or
certify the approximation against NLHE/an external GTO reference.
"""
import gzip,base64,hashlib,json,math,sqlite3,zlib
from pathlib import Path
from gto.abstract import joint_stream as s

def certificate(root):
    root=Path(root)
    db=sqlite3.connect((root/'policy.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    get=lambda k:zlib.decompress(db.execute('select value from state where key=?',(k,)).fetchone()[0])
    meta=json.loads(get('meta'));stats=json.loads(get('verify'))
    out={'meta':meta,'oracle':s.unpack(get('oracle')),'stats':stats,
         'policy_state_digest':hashlib.sha256(b''.join(k.encode()+hashlib.sha256(v).digest() for k,v in db.execute('select key,value from state order by key'))).hexdigest()}
    db.close();return out

def check(cert,result,tolerance=1e-8):
    meta=cert['meta'];v=cert['oracle'];stats=cert['stats']
    if meta!=result['meta'] or meta['phase']!='verify' or meta['cursor']!=1755 or not result['complete']:raise ValueError('incomplete/inconsistent population certificate')
    if len(v)!=6 or len(stats['ev'])!=2 or not all(math.isfinite(x) for x in v+stats['ev']):raise ValueError('finite measured values required')
    if not stats['bins'] or any(key.split('/')[0] not in ('0','1') or not math.isfinite(g) or not math.isfinite(reach) or reach<0 for key,(g,reach) in stats['bins'].items()):raise ValueError('finite legal attribution required')
    expected=[v[2]-v[5],v[3]+v[5]]
    realized=[stats['ev'][0]-v[5],v[5]-stats['ev'][1]]
    attributed=[math.fsum(g for key,(g,reach) in stats['bins'].items() if int(key.split('/')[0])==o) for o in (0,1)]
    errors=[abs(a-b) for a,b in zip(expected,realized)]+[abs(a-b) for a,b in zip(realized,attributed)]+[abs(v[0]-v[2]),abs(v[1]-v[3]),abs(v[4]-v[5])]
    for key,actual in [('independent_br_gains_bb',expected),('realized_br_gains_bb',realized),('attributed_gains_bb',attributed)]:
        if len(result[key])!=2 or not all(math.isfinite(x) for x in result[key]):raise ValueError('complete player measurements required')
        errors.extend(abs(a-b) for a,b in zip(actual,result[key]))
    errors.append(abs(sum(expected)-result['nashconv_bb']))
    if max(errors)>tolerance or meta['max_native_error']>tolerance or not result['pass_tolerance']:raise ValueError('independent realization/BR/attribution mismatch')
    if result['normal_GTO_added']!=0 or result['formal_acceptance']!=[0,12] or result['external_GTO']!='NOT PERFORMED' or result['real_game_error']!='UNKNOWN':raise ValueError('unsupported qualification/promotion')
    return {'max_recomputed_error_bb':max(errors),'nashconv_bb':sum(expected),'br_gains_bb':expected,'population_orbits':1755,'physical_flops':22100,'scope':'MEASURED_RESTRICTED_GAME_ONLY;SHORT_CI_DOES_NOT_REPLAY_KERNELS'}

def write(root,destination):
    cert=certificate(root);result=json.loads((Path(root)/'result.json').read_text());checked=check(cert,result)
    raw=json.dumps(cert,sort_keys=True,separators=(',',':')).encode()
    Path(destination).write_bytes(base64.b64encode(gzip.compress(raw,mtime=0))+b'\n')
    return {**checked,'raw_certificate_sha256':hashlib.sha256(raw).hexdigest()}

def read(path):return json.loads(gzip.decompress(base64.b64decode(Path(path).read_bytes())))
