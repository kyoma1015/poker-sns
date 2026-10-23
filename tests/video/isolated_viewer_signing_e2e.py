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
    print("PASS: isolated owner JWT + RLS signed URL issuance, viewer denied")

if __name__ == "__main__":
    main()
