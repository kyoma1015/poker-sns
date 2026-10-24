"""Isolated-only end-to-end Auth -> private Storage -> ffprobe -> PostgREST.

Run only against the fixed local Supabase API on loopback. Does not activate
video posting. The test creates and deletes its own local user/media.
"""
import json
from concurrent.futures import ThreadPoolExecutor
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
        # Exercise the actual isolated POST endpoint, not only its Python function.
        from tests.video.isolated_video_http import make_local_server as make_finalize_server
        from threading import Thread as FinalizeThread
        from urllib.error import HTTPError
        finalize_server = make_finalize_server(key, service)
        finalize_thread = FinalizeThread(target=finalize_server.serve_forever, daemon=True)
        finalize_thread.start()
        try:
            finalize_url = ("http://127.0.0.1:" + str(finalize_server.server_port)
                            + "/video/finalize")
            def post_finalize(headers, body):
                return Request(finalize_url, data=json.dumps(body).encode(),
                               headers=headers, method="POST")
            valid_headers = {"Authorization": "Bearer " + session,
                             "Content-Type": "application/json"}
            with urlopen(post_finalize(valid_headers,
                                      {"object_path": path, "content": "real E2E"}),
                         timeout=20) as response:
                assert json.load(response) == first
                assert response.headers.get("Cache-Control") == "no-store, private"
            # Finalize a NEW staged object via HTTP, not via direct Python
            # invocation. This proves the endpoint can commit a fresh post.
            fresh_path = owner + "/" + str(uuid4()) + ".mp4"
            fresh_upload = Request(
                API + "/storage/v1/object/post-videos/" + fresh_path,
                data=media.read_bytes(),
                headers={"Authorization": "Bearer " + session,
                         "apikey": key, "Content-Type": "video/mp4",
                         "x-upsert": "false"}, method="POST")
            with urlopen(fresh_upload, timeout=20) as response:
                assert response.status in (200, 201)
            fresh_body = {"object_path": fresh_path, "content": "HTTP-first publish"}
            with urlopen(post_finalize(valid_headers, fresh_body), timeout=20) as response:
                fresh_post = json.load(response)
                assert response.headers.get("Cache-Control") == "no-store, private"
            assert fresh_post["post_id"] != first["post_id"]
            with urlopen(post_finalize(valid_headers, fresh_body), timeout=20) as response:
                assert json.load(response) == fresh_post
            from tests.video.isolated_db_adapter import reconcile_post as reconcile_http_post
            assert reconcile_http_post(API, service, owner, fresh_path) == fresh_post["post_id"]
            # Playback of the HTTP-first post must use the same server and
            # re-check authorization; the endpoint must not return a signed URL.
            from urllib.parse import urlencode as encode_fresh_query
            fresh_video_url = (
                "http://127.0.0.1:" + str(finalize_server.server_port)
                + "/video?" + encode_fresh_query({"post_id": fresh_post["post_id"]}))
            with urlopen(Request(
                fresh_video_url, headers={"Authorization": "Bearer " + session}),
                timeout=20) as response:
                assert response.status == 200
                assert response.read() == media.read_bytes()
                assert response.headers.get("Cache-Control") == "no-store, private"
                assert response.headers.get("Vary") == "Authorization"
                assert response.headers.get("Location") is None
            try:
                urlopen(Request(fresh_video_url), timeout=10)
            except HTTPError as exc:
                try:
                    assert exc.code in (401, 403)
                finally:
                    exc.close()
            else:
                raise AssertionError("HTTP-first post playback bypassed JWT")
            print("PASS: HTTP-first post -> same-origin authorized GET bytes; no redirect")
            print("PASS: real HTTP POST creates a NEW isolated video post and idempotent retry")
            for headers, payload in (
                ({"Content-Type": "application/json"}, {"object_path": path, "content": "real E2E"}),
                ({"Authorization": "Bearer invalid", "Content-Type": "application/json"},
                 {"object_path": path, "content": "real E2E"}),
                (valid_headers, {"object_path": path, "content": "real E2E", "user_id": owner}),
                (valid_headers, {"object_path": "20000000-0000-0000-0000-000000000002/"
                                 + path.split("/", 1)[1], "content": "real E2E"}),
            ):
                try:
                    urlopen(post_finalize(headers, payload), timeout=20)
                except HTTPError as exc:
                    try:
                        assert exc.code in (401, 403), exc.code
                    finally:
                        exc.close()
                else:
                    raise AssertionError("isolated HTTP finalize accepted unauthorized input")
            # The same authenticated caller can finalize a staged clip only;
            # a different verified user must not publish the owner's object.
            other_auth = request_json("/auth/v1/signup", {
                "email": "video-other-" + str(uuid4()) + "@example.invalid",
                "password": "video-isolated-test-Password1!"
            }, key)
            other_token = other_auth.get("access_token") or (
                other_auth.get("session") or {}).get("access_token")
            assert other_token
            try:
                urlopen(post_finalize(
                    {"Authorization": "Bearer " + other_token,
                     "Content-Type": "application/json"},
                    {"object_path": path, "content": "cross-owner denied"}), timeout=20)
            except HTTPError as exc:
                try:
                    assert exc.code == 403, exc.code
                finally:
                    exc.close()
            else:
                raise AssertionError("another authenticated user finalized owner's video")
            # The same HTTP listener must serve freshly authorized media after
            # finalization; no redirect or signed Storage URL is returned.
            from urllib.parse import urlencode as encode_video_query
            same_origin_video = (
                "http://127.0.0.1:" + str(finalize_server.server_port)
                + "/video?" + encode_video_query({"post_id": first["post_id"]}))
            with urlopen(Request(
                same_origin_video,
                headers={"Authorization": "Bearer " + session}), timeout=20) as response:
                assert response.read() == media.read_bytes()
                assert response.headers.get("Cache-Control") == "no-store, private"
                assert response.headers.get("Vary") == "Authorization"
            try:
                urlopen(Request(same_origin_video), timeout=10)
            except HTTPError as exc:
                try:
                    assert exc.code in (401, 403)
                finally:
                    exc.close()
            else:
                raise AssertionError("combined HTTP server exposed video without JWT")
            # A real second JWT is not sufficient to read a private post.
            try:
                urlopen(Request(
                    same_origin_video,
                    headers={"Authorization": "Bearer " + other_token}), timeout=20)
            except HTTPError as exc:
                try:
                    assert exc.code == 403, exc.code
                finally:
                    exc.close()
            else:
                raise AssertionError("private finalized video exposed to another JWT")
            print("PASS: same-origin HTTP playback rejects a different valid JWT")
            print("PASS: same isolated HTTP origin finalizes and serves freshly JWT-authorized video")
            print("PASS: isolated HTTP POST denies cross-account staged object finalization")
            print("PASS: isolated HTTP POST finalization is idempotent and rejects unauthorized requests")
        finally:
            finalize_server.shutdown()
            finalize_server.server_close()
            finalize_thread.join(timeout=5)
        from tests.video.isolated_db_adapter import publish_post, reconcile_post
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(
                lambda unused: publish_post(API, service, owner, path, "real E2E"),
                range(16),
            ))
        if set(results) != {first["post_id"]}:
            raise AssertionError("concurrent publish returned conflicting post IDs")
        if reconcile_post(API, service, owner, path) != first["post_id"]:
            raise AssertionError("committed post reconciliation mismatch")
        # Full journey: the finalized post is visible to its authenticated owner,
        # its video path is the uploaded immutable object, and the playback
        # proxy returns the exact original media bytes after a fresh RLS check.
        from urllib.parse import urlencode
        from tests.video.isolated_authorized_media_proxy import fetch_visible_video
        query = urlencode({"id": "eq." + first["post_id"],
                           "select": "id,user_id,content,video_path"})
        owner_view = Request(API + "/rest/v1/posts?" + query,
                             headers={"apikey": key,
                                      "Authorization": "Bearer " + session})
        with urlopen(owner_view, timeout=10) as response:
            rows = json.load(response)
        if len(rows) != 1 or rows[0]["user_id"] != owner or rows[0]["video_path"] != path:
            raise AssertionError("finalized video not visible in owner timeline/detail")
        delivered = fetch_visible_video(API, key, service, session, first["post_id"])
        if delivered != media.read_bytes():
            raise AssertionError("authorized playback bytes differ from uploaded media")
        # Verify the finalized post via the actual authenticated HTTP boundary.
        from tests.video.isolated_authorized_media_http import make_local_server
        from threading import Thread
        server = make_local_server(key, service)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            playback_url = ("http://127.0.0.1:" + str(server.server_port)
                            + "/video?" + urlencode({"post_id": first["post_id"]}))
            playback_request = Request(
                playback_url, headers={"Authorization": "Bearer " + session})
            with urlopen(playback_request, timeout=20) as response:
                if response.read() != media.read_bytes():
                    raise AssertionError("HTTP playback bytes differ from uploaded media")
                if response.headers.get("Cache-Control") != "no-store, private":
                    raise AssertionError("authenticated HTTP playback may be cached")
                if response.headers.get("Vary") != "Authorization":
                    raise AssertionError("authenticated HTTP playback missing Vary")
            from urllib.error import HTTPError
            for invalid_header in ({}, {"Authorization": "Bearer invalid"}):
                try:
                    urlopen(Request(playback_url, headers=invalid_header), timeout=10)
                except HTTPError as exc:
                    try:
                        if exc.code not in (401, 403):
                            raise AssertionError("HTTP playback returned unexpected auth status")
                    finally:
                        exc.close()
                else:
                    raise AssertionError("finalized video exposed without valid JWT")
            print("PASS: integrated finalized post -> real authenticated HTTP playback and unauthorized denial")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        print("PASS: integrated video journey upload -> ffprobe -> authenticated DB publish -> owner feed/detail -> authorized media playback")
        print("PASS: isolated concurrent PostgREST publish and reconciliation")
        print("PASS: real isolated Auth -> private Storage -> ffprobe -> DB publish -> idempotent retry")
if __name__ == "__main__":
    main()
