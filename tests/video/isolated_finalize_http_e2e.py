"""Isolated-only end-to-end Auth -> private Storage -> ffprobe -> PostgREST.

Run only against the fixed local Supabase API on loopback. Does not activate
video posting. The test creates and deletes its own local user/media.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4
from urllib.request import Request, urlopen

from tests.video.finalize_boundary import finalize_authenticated
from tests.video.isolated_composition import build_isolated_adapters

API = "http://127.0.0.1:56321"

def request_json(route, payload, key, token=None):
    headers = {"apikey": key, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(API + route, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urlopen(req, timeout=20) as resp:
        return json.load(resp)

def main():
    env = {}
    for line in Path(os.environ["VIDEO_QA_ENV"]).read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            env[k] = v.strip('"\'')
    key = env.get("ANON_KEY") or env.get("PUBLISHABLE_KEY")
    service = env.get("SERVICE_ROLE_KEY")
    if not key or not service:
        raise RuntimeError("missing local credentials")
    suffix = str(uuid4())
    auth = request_json("/auth/v1/signup", {
        "email": "video-e2e-" + suffix + "@example.invalid",
        "password": "video-isolated-test-Password1!"
    }, key)
    user = auth.get("user") or {}
    session = auth.get("access_token") or (auth.get("session") or {}).get("access_token")
    owner = user.get("id")
    if not owner or not session:
        raise RuntimeError("isolated signup did not issue a session")
    with tempfile.TemporaryDirectory() as tmp:
        media = Path(tmp) / "clip.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                        "-i", "color=c=black:s=64x64:r=5:d=1", "-c:v", "mpeg4",
                        "-y", str(media)], check=True, timeout=20)
        path = owner + "/" + str(uuid4()) + ".mp4"
        upload = Request(API + "/storage/v1/object/post-videos/" + path,
                         data=media.read_bytes(),
                         headers={"Authorization": "Bearer " + session,
                                  "apikey": key, "Content-Type": "video/mp4",
                                  "x-upsert": "false"}, method="POST")
        with urlopen(upload, timeout=20) as resp:
            if resp.status not in (200, 201):
                raise RuntimeError("isolated upload rejected")
        adapters = build_isolated_adapters(project_url=API, anon_key=key,
                                           service_key=service, access_token=session)
        first = finalize_authenticated("Bearer " + session,
                                       {"object_path": path, "content": "real E2E"}, adapters)
        second = finalize_authenticated("Bearer " + session,
                                        {"object_path": path, "content": "real E2E"}, adapters)
        if first != second:
            raise AssertionError("non-idempotent full finalization")
        print("PASS: real isolated Auth -> private Storage -> ffprobe -> DB publish -> idempotent retry")
if __name__ == "__main__":
    main()
