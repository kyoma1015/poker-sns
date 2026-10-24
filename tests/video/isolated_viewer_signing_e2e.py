"""Real isolated owner-only signed URL issuance E2E."""
import json
import os
from pathlib import Path
from urllib.request import urlopen
from uuid import uuid4
from urllib.error import HTTPError
from tests.video.isolated_finalize_http_e2e import API, request_json
from tests.video.isolated_db_adapter import publish_post
from tests.video.isolated_viewer_signing import issue_owner_video_url

def main():
    env = {}
    for line in Path(os.environ["VIDEO_QA_ENV"]).read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            env[k] = v.strip('"\'')
    key = env.get("ANON_KEY") or env.get("PUBLISHABLE_KEY")
    service = env["SERVICE_ROLE_KEY"]
    tokens = []
    for name in ("owner", "viewer"):
        auth = request_json("/auth/v1/signup", {
            "email": "sign-" + name + "-" + str(uuid4()) + "@example.invalid",
            "password": "video-isolated-test-Password1!",
        }, key)
        tokens.append((auth["user"]["id"], auth["access_token"]))
    owner, owner_token = tokens[0]
    viewer, viewer_token = tokens[1]
    path = owner + "/" + str(uuid4()) + ".mp4"
    from urllib.request import Request
    media = b"isolated-signed-url-authorization-test"
    req = Request(API + "/storage/v1/object/post-videos/" + path,
                  data=media, headers={"apikey": key,
                                      "Authorization": "Bearer " + owner_token,
                                      "Content-Type": "video/mp4"}, method="POST")
    with urlopen(req, timeout=10) as response:
        assert response.status in (200, 201)
    post_id = publish_post(API, service, owner, path, "owner signing E2E")
    signed = issue_owner_video_url(API, key, owner_token, post_id)
    with urlopen(signed, timeout=10) as response:
        assert response.read() == media
    try:
        issue_owner_video_url(API, key, viewer_token, post_id)
    except (PermissionError, HTTPError):
        pass
    else:
        raise AssertionError("other user obtained owner signed URL")
    from tests.video.isolated_visible_signing import issue_visible_video_url
    from tests.video.isolated_db_adapter import _rpc
    from urllib.request import Request
    def set_visibility(is_public):
        req = Request(API + "/rest/v1/posts?id=eq." + post_id,
                      data=json.dumps({"is_public": is_public}).encode(),
                      headers={"apikey": service, "Authorization": "Bearer " + service,
                               "Content-Type": "application/json"}, method="PATCH")
        with urlopen(req, timeout=10) as response:
            assert response.status in (200, 204)
    try:
        issue_visible_video_url(API, key, service, viewer_token, post_id)
    except (PermissionError, HTTPError):
        pass
    else:
        raise AssertionError("private post exposed to other viewer")
    set_visibility(True)
    public_url = issue_visible_video_url(API, key, service, viewer_token, post_id)
    with urlopen(public_url, timeout=10) as response:
        assert response.read() == media
    from tests.video.isolated_authorized_media_proxy import fetch_visible_video
    assert fetch_visible_video(API, key, service, viewer_token, post_id) == media
    from tests.video.isolated_authorized_media_http import make_local_server
    from threading import Thread
    from urllib.parse import urlencode
    http_server = make_local_server(key, service)
    thread = Thread(target=http_server.serve_forever, daemon=True)
    thread.start()
    url = "http://127.0.0.1:" + str(http_server.server_port) + "/video?" + urlencode({"post_id": post_id})
    def media_request(token):
        return Request(url, headers={"Authorization": "Bearer " + token})
    try:
        with urlopen(media_request(viewer_token), timeout=10) as response:
            assert response.read() == media
            assert response.headers.get("Cache-Control") == "no-store, private"
            assert response.headers.get("Vary") == "Authorization"
            assert response.headers.get("Pragma") == "no-cache"
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=8) as pool:
            def fetch_once(_):
                with urlopen(media_request(viewer_token), timeout=10) as response:
                    assert response.headers.get("Cache-Control") == "no-store, private"
                    assert response.headers.get("X-Content-Type-Options") == "nosniff"
                    return response.read()
            assert all(result == media for result in pool.map(fetch_once, range(16)))
        print("PASS: 16 concurrent authorized HTTP media reads with no-store")
        for headers in ({}, {"Authorization": "Bearer invalid"}):
            try:
                urlopen(Request(url, headers=headers), timeout=10)
            except HTTPError as exc:
                try:
                    assert exc.code in (401, 403)
                finally:
                    exc.close()
            else:
                raise AssertionError("unauthenticated media request accepted")
        for bad_id in ("not-a-uuid", "00000000-0000-0000-0000-000000000000"):
            bad_url = "http://127.0.0.1:" + str(http_server.server_port) + "/video?" + urlencode({"post_id": bad_id})
            try:
                urlopen(Request(bad_url, headers={"Authorization": "Bearer " + viewer_token}), timeout=10)
            except HTTPError as exc:
                try:
                    assert exc.code == 403
                finally:
                    exc.close()
            else:
                raise AssertionError("invalid or nonexistent post served")
        print("PASS: isolated HTTP proxy rejects invalid and missing post IDs")
        set_visibility(False)
        try:
            urlopen(media_request(viewer_token), timeout=10)
        except HTTPError as exc:
            try:
                assert exc.code == 403
            finally:
                exc.close()
        else:
            raise AssertionError("HTTP endpoint served revoked viewer")
        with urlopen(media_request(owner_token), timeout=10) as response:
            assert response.read() == media
        print("PASS: isolated HTTP media endpoint enforces JWT/RLS after privacy change")
    finally:
        http_server.shutdown()
        http_server.server_close()
        thread.join(timeout=5)
    try:
        fetch_visible_video(API, key, service, viewer_token, post_id)
    except (PermissionError, HTTPError):
        pass
    else:
        raise AssertionError("private video still served after privacy transition")
    assert fetch_visible_video(API, key, service, owner_token, post_id) == media
    print("PASS: isolated JWT/RLS media proxy denies revoked viewer on next request")
    # A previously issued signed URL is a bearer capability. The privacy
    # transition blocks NEW issuance, not the existing token.
    with urlopen(public_url, timeout=10) as response:
        assert response.read() == media
    print("PASS: existing signed URL survives privacy transition; immediate revocation BLOCKED")
    try:
        issue_visible_video_url(API, key, service, viewer_token, post_id)
    except (PermissionError, HTTPError):
        pass
    else:
        raise AssertionError("private transition not enforced")
    print("PASS: isolated public viewer JWT + RLS signed URL and private denial")
    print("PASS: isolated owner JWT + RLS signed URL issuance, viewer denied")

if __name__ == "__main__":
    main()
