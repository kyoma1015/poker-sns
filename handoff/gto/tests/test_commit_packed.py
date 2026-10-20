"""Isolated TASK GTO-HANDOFF-10 tests; no network/native imports."""
from pathlib import Path
import hashlib, importlib.util, json, sqlite3, struct, tempfile, traceback, sys

ROOT=Path(__file__).resolve().parent
EXPECTED="9d166dfbd0d9da199585de631788e03636c295f595d568451239f0c0e652da52"
assert hashlib.sha256((ROOT/"packed_backend.py").read_bytes()).hexdigest()==EXPECTED
spec=importlib.util.spec_from_file_location("packed_backend", ROOT/"packed_backend.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
Backend=module.LiveBackend
results=[]
def u(n): return struct.pack("<Q",n)
def encode(rows):
    return u(len(rows))+b"".join(u(len(k))+u(len(v))+k+v for k,v in rows)
def snapshot(conn):
    return {"rows":[(bytes(k).hex(),bytes(v).hex(),bytes(d).hex()) for k,v,d in conn.execute("SELECT k,data,digest FROM rows ORDER BY k")],
            "meta":list(conn.execute("SELECT k,v FROM meta ORDER BY k"))}
def record(name, expected, actual, condition):
    results.append({"name":name,"expected":expected,"actual":actual,"status":"PASS" if condition else "FAIL"})
    print(results[-1]["status"],name,json.dumps(actual,ensure_ascii=False))
def check(name,expected,fn):
    try:
        actual=fn()
        record(name,expected,actual,True)
    except Exception as e:
        record(name,expected,{"unexpected_exception":repr(e),"traceback":traceback.format_exc()},False)

def normal(name,rows,overwrite=False):
    with tempfile.TemporaryDirectory(prefix="sqlite-",dir=ROOT) as td:
        b=Backend(Path(td)/"test.sqlite")
        try:
            b.initialize("task10")
            if overwrite:
                b.begin();b.commit_packed(encode([(rows[0][0],b"old")]),"old-rng",1,1)
            b.begin();b.commit_packed(encode(rows),"rng-v2",17,123)
            expected=dict(rows)
            for k,v in expected.items(): assert b.get(k)==v
            assert b.count()==len(expected)
            for k,v,d in b.db.execute("SELECT k,data,digest FROM rows"):
                assert bytes(d)==hashlib.sha256(bytes(v)).digest()
            assert b.initialize("task10")== (17,123,"rng-v2")
            assert not b.active and not b.db.in_transaction
            with sqlite3.connect(b.path) as other:
                assert snapshot(other)==snapshot(b.db)
            return {"rows":b.count(),"readback_equal":True,"digests_equal":True,
                    "meta":[17,123,"rng-v2"],"other_connection_equal":True}
        finally:b.close()

normal_cases=[
 ("N01_one_row",[(b"k",b"v")],False),
 ("N02_multiple_rows",[(b"a",b"1"),(b"b",b"2"),(b"c",b"3")],False),
 *[(f"N_boundary_{n}",[(str(i).encode(),(f"value-{i}").encode()) for i in range(n)],False) for n in (255,256,257)],
 ("N06_replace_key",[(b"k",b"new")],True),
 ("N07_empty_rows",[],False),
 ("N08_binary",[(b"\x00\xff\x80",b"\x00\xfe\xff\x80")],False),
 ("N09_metadata",[(b"m",b"x")],False),
 ("N10_value_digest",[(b"d",bytes(range(256)))],False),
 ("N11_other_connection",[(b"o",b"visible")],False),
]
for name,rows,overwrite in normal_cases:
    check(name,"行・値・digest・metadataが一致しCOMMIT後に別接続から可視",
          lambda rows=rows,overwrite=overwrite: normal(name,rows,overwrite))

bad_cases=[
 ("E01_empty_input",b"",ValueError,"truncated packed batch",True),
 ("E02_seven_bytes",b"\0"*7,ValueError,"truncated packed batch",True),
 ("E03_row_count_cap",u(1_000_001),ValueError,"packed row count cap",True),
 ("E04_key_length_cap",u(1)+u(1_048_577)+u(0),ValueError,"invalid packed row length",True),
 ("E05_value_length_cap",u(1)+u(0)+u(64_000_001),ValueError,"invalid packed row length",True),
 ("E06_truncated_key",u(1)+u(3)+u(0)+b"ab",ValueError,"invalid packed row length",True),
 ("E07_truncated_value",u(1)+u(1)+u(3)+b"kab",ValueError,"invalid packed row length",True),
 ("E08_trailing_bytes",encode([(b"x",b"y")])+b"\xff",ValueError,"trailing packed bytes",True),
 ("E09_no_transaction",encode([(b"x",b"y")]),RuntimeError,"no active transaction",False),
]
def abnormal(payload,typ,message,active):
    with tempfile.TemporaryDirectory(prefix="sqlite-",dir=ROOT) as td:
        b=Backend(Path(td)/"test.sqlite")
        try:
            b.initialize("task10");b.begin()
            b.commit_packed(encode([(b"stable",b"committed")]),"stable-rng",5,9)
            before=snapshot(b.db)
            if active:b.begin()
            try:b.commit_packed(payload,"bad-rng",99,99)
            except typ as e:
                assert str(e)==message
                actual_error=type(e).__name__+": "+str(e)
            else:raise AssertionError("expected exception missing")
            before_rollback={"active":b.active,"in_transaction":b.db.in_transaction}
            b.rollback()
            assert snapshot(b.db)==before
            with sqlite3.connect(b.path) as other:assert snapshot(other)==before
            return {"exception":actual_error,"before_caller_rollback":before_rollback,
                    "committed_snapshot_preserved":True,"after_rollback_active":b.active}
        finally:b.close()
for name,payload,typ,msg,active in bad_cases:
    check(name,f"{typ.__name__}: {msg}、呼出元rollback後に元の確定状態と一致",
          lambda p=payload,t=typ,m=msg,a=active:abnormal(p,t,m,a))

# Force one full 256-row batch to execute before the malformed 257th row.
try:
    with tempfile.TemporaryDirectory(prefix="atomic-",dir=ROOT) as td:
        b=Backend(Path(td)/"test.sqlite")
        try:
            b.initialize("atomic");b.begin()
            b.commit_packed(encode([(b"stable",b"committed")]),"stable-rng",5,9)
            baseline=snapshot(b.db)
            pending=[(f"new-{i:03d}".encode(),b"value") for i in range(256)]
            bad=u(257)+encode(pending)[8:]+u(1)+u(2)+b"x"  # missing 2-byte value
            b.begin()
            error=None
            try:b.commit_packed(bad,"new-rng",100,200)
            except ValueError as e:error=str(e)
            record("A01_exception_after_partial_batch","ValueErrorがメソッド内部で発生",
                   {"error":error},error=="invalid packed row length")
            count=b.count()
            record("A02_not_automatically_rolled_back","同接続に未確定256行が残りtransactionがactive",
                   {"own_rows":count,"active":b.active,"in_transaction":b.db.in_transaction},
                   count==257 and b.active and b.db.in_transaction)
            with sqlite3.connect(b.path) as other:
                visible=snapshot(other)
            record("A03_no_external_partial_commit","別接続は元の確定状態だけを観測",
                   {"observer_rows":len(visible["rows"]),"baseline_equal":visible==baseline},
                   visible==baseline)
            b.rollback()
            record("A04_caller_rollback_succeeds","呼出元rollbackが成功しtransaction終了",
                   {"active":b.active,"in_transaction":b.db.in_transaction},
                   not b.active and not b.db.in_transaction)
            with sqlite3.connect(b.path) as other:
                after=snapshot(other)
            record("A05_no_partial_rows_and_preserved_commit","新規部分行0、元の行・digest・metadataを保持",
                   {"own_rows":b.count(),"observer_rows":len(after["rows"]),
                    "snapshot_equal":snapshot(b.db)==after==baseline,
                    "writes_counter":b.writes},
                   snapshot(b.db)==after==baseline and b.count()==1)
        finally:b.close()
except Exception as e:
    record("A_UNEXPECTED","原子性検証を完了",repr(e),False)
summary={status:sum(r["status"]==status for r in results) for status in ("PASS","FAIL","BLOCKED")}
report={"task":"GTO-HANDOFF-10","source_sha256":EXPECTED,
        "python":sys.version,"sqlite":sqlite3.sqlite_version,
        "test_count":len(results),"summary":summary,"results":results}
(ROOT/"results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
print("SUMMARY",json.dumps(summary),"TOTAL",len(results))
assert hashlib.sha256((ROOT/"packed_backend.py").read_bytes()).hexdigest()==EXPECTED
sys.exit(1 if summary["FAIL"] else 0)
