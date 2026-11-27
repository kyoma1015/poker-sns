#!/usr/bin/env python3
"""Exercise a synthetic restore on two disposable local Supabase instances."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

ROOT = Path(__file__).resolve().parents[1]
CLI = ["npx", "--yes", "supabase@2.81.3"]
API = "http://127.0.0.1:56321"
DB = "supabase_db_pokerid-video-isolated"
STACK = ROOT / "tests/video/local-stack"
PASSWORD = "synthetic-restore-fixture-password"
FILES = {"one.txt": b"synthetic one\n", "nested/two.txt": b"synthetic two\n"}
OWNER = "restore-owner@example.com"
OTHER = "restore-other@example.com"


class RejectRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


HTTP = build_opener(ProxyHandler({}), RejectRedirect())


def command(*args, data=None):
    return subprocess.run(args, input=data, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, timeout=360).stdout


def stack(*args):
    return command(*CLI, *args, "--workdir", str(STACK))


def start():
    stack("start", "--exclude", "studio,imgproxy,mailpit,edge-runtime,realtime,vector,logflare")
    env = stack("status", "-o", "env").decode().splitlines()
    values = dict(line.split("=", 1) for line in env if "=" in line)
    if values.get("API_URL", "").strip('"') != API:
        raise ValueError("unexpected local API")
    return values["ANON_KEY"].strip('"')


def pg(*args, data=None):
    return command("docker", "exec", "-i", DB, *args, data=data)


def sql(statement):
    return pg("psql", "-XAt", "-U", "postgres", "-v", "ON_ERROR_STOP=1", "-c", statement)


def req(path, key, token=None, body=None, method="GET", expected=200, content_type="application/json"):
    headers = {"apikey": key, "Authorization": "Bearer " + (token or key),
               "Content-Type": content_type}
    try:
        with HTTP.open(Request(API + path, body, headers, method=method), timeout=15) as response:
            status, content = response.status, response.read()
    except HTTPError as error:
        status, content = error.code, b""
    if status not in ((expected,) if isinstance(expected, int) else expected):
        raise ValueError("unexpected local HTTP status")
    return content


def auth(path, email, key):
    data = json.dumps({"email": email, "password": PASSWORD}).encode()
    return json.loads(req("/auth/v1/" + path, key, body=data, method="POST"))


def storage_init():
    sql("""
        insert into storage.buckets(id, name, public) values ('restore-fixture', 'restore-fixture', false);
        create policy restore_fixture_insert on storage.objects for insert to authenticated
          with check (bucket_id = 'restore-fixture' and split_part(name, '/', 1) = auth.uid()::text);
        create policy restore_fixture_read on storage.objects for select to authenticated
          using (bucket_id = 'restore-fixture' and owner_id = auth.uid()::text);
    """)


def upload(key, actor, name, data):
    path = "/storage/v1/object/restore-fixture/" + actor["user"]["id"] + "/" + name
    req(path, key, actor["access_token"], data, "POST", content_type="text/plain")


def download(key, actor, owner, name, expected=200):
    path = "/storage/v1/object/authenticated/restore-fixture/" + owner + "/" + name
    return req(path, key, actor["access_token"], expected=expected)


def main():
    os.umask(0o077)
    stage = "SOURCE_START"
    try:
        key = start()
        owner = auth("signup", OWNER, key)
        auth("signup", OTHER, key)
        owner_id = owner["user"]["id"]
        if not re.fullmatch(r"[0-9a-f-]{36}", owner_id):
            raise ValueError("unexpected user ID")
        stage = "SOURCE_FIXTURES"
        storage_init()
        sql(f"""
            create table public.restore_fixture (id integer primary key, owner_id uuid references auth.users(id));
            insert into public.restore_fixture values (1, '{owner_id}');
            alter table public.restore_fixture enable row level security;
            grant select on public.restore_fixture to authenticated;
            create policy restore_fixture_owner on public.restore_fixture for select to authenticated
              using (owner_id = auth.uid());
        """)
        for name, data in FILES.items():
            upload(key, owner, name, data)
        stage = "SYNTHETIC_BACKUP"
        auth_dump = pg("pg_dump", "-U", "postgres", "--data-only", "-t", "auth.users", "-t", "auth.identities")
        db_dump = pg("pg_dump", "-U", "postgres", "-Fc", "-t", "public.restore_fixture")
        with tempfile.TemporaryDirectory() as directory:
            backup = Path(directory)
            (backup / "auth.sql").write_bytes(auth_dump)
            (backup / "db.dump").write_bytes(db_dump)
            for index, name in enumerate(FILES):
                (backup / str(index)).write_bytes(download(key, owner, owner_id, name))
            digests = {file.name: hashlib.sha256(file.read_bytes()).digest() for file in backup.iterdir()}
            for index, data in enumerate(FILES.values()):
                if digests[str(index)] != hashlib.sha256(data).digest():
                    raise ValueError("source inventory digest mismatch")
            stage = "TARGET_START"
            stack("stop", "--no-backup")
            key = start()
            if sql("select count(*) from auth.users").strip() != b"0" or sql(
                "select to_regclass('public.restore_fixture') is null"
            ).strip() != b"t":
                raise ValueError("target was not fresh")
            stage = "TARGET_RESTORE"
            for item, digest in digests.items():
                if hashlib.sha256((backup / item).read_bytes()).digest() != digest:
                    raise ValueError("backup digest mismatch")
            pg("psql", "-X", "-U", "postgres", "-v", "ON_ERROR_STOP=1", data=(backup / "auth.sql").read_bytes())
            pg("pg_restore", "-U", "postgres", "--exit-on-error", "-d", "postgres", data=(backup / "db.dump").read_bytes())
            storage_init()
            stage = "AUTH_RLS_STORAGE_VERIFY"
            owner = auth("token?grant_type=password", OWNER, key)
            other = auth("token?grant_type=password", OTHER, key)
            if owner["user"]["id"] != owner_id or owner_id == other["user"]["id"]:
                raise ValueError("auth identity mismatch")
            path = "/rest/v1/restore_fixture?select=id,owner_id"
            if json.loads(req(path, key, owner["access_token"])) != [{"id": 1, "owner_id": owner_id}]:
                raise ValueError("owner RLS mismatch")
            if json.loads(req(path, key, other["access_token"])) != []:
                raise ValueError("non-owner RLS mismatch")
            for index, name in enumerate(FILES):
                upload(key, owner, name, (backup / str(index)).read_bytes())
                if hashlib.sha256(download(key, owner, owner_id, name)).digest() != digests[str(index)]:
                    raise ValueError("restored object digest mismatch")
                download(key, other, owner_id, name, expected=(400, 403, 404))
            if sql("select count(*) from storage.objects where bucket_id = 'restore-fixture'").strip() != b"2":
                raise ValueError("restored inventory count mismatch")
        print("PASS: synthetic PostgreSQL, Auth, Storage, RLS and all object SHA-256")
    except (KeyError, OSError, ValueError, subprocess.SubprocessError):
        raise SystemExit("FAIL: " + stage) from None
    finally:
        try:
            stack("stop", "--no-backup")
        except (OSError, subprocess.SubprocessError):
            raise SystemExit("FAIL: LOCAL_STACK_CLEANUP") from None


if __name__ == "__main__":
    main()
