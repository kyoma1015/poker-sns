#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
ffmpeg -hide_banner -loglevel error -f lavfi -i color=c=black:s=32x32:r=1 -t 2 -c:v libx264 -pix_fmt yuv420p -y "$work/valid.mp4"
ffmpeg -hide_banner -loglevel error -f lavfi -i color=c=black:s=32x32:r=1 -t 31 -c:v libx264 -pix_fmt yuv420p -y "$work/long.mp4"
python3 tests/video/server_validate.py "$work/valid.mp4"
if python3 tests/video/server_validate.py "$work/long.mp4"; then echo "FAIL: 31s accepted"; exit 1; fi
cp "$work/valid.mp4" "$work/fake.webm"
if python3 tests/video/server_validate.py "$work/fake.webm"; then echo "FAIL: fake WebM accepted"; exit 1; fi
printf 'not a video' > "$work/bad.mp4"
if python3 tests/video/server_validate.py "$work/bad.mp4"; then echo "FAIL: malformed MP4 accepted"; exit 1; fi
truncate -s 20971521 "$work/oversize.mp4"
if python3 tests/video/server_validate.py "$work/oversize.mp4"; then echo "FAIL: oversize accepted"; exit 1; fi
echo 'PASS: isolated ffprobe 2s accept, 31s reject, spoofed/malformed/oversize reject'
