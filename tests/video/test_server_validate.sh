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
# Matroska containers can masquerade as WebM; reject incompatible codecs.
ffmpeg -hide_banner -loglevel error -f lavfi -i color=c=black:s=32x32:r=1 -t 2 -c:v libx264 -y "$work/h264.mkv"
cp "$work/h264.mkv" "$work/fake-codec.webm"
if python3 tests/video/server_validate.py "$work/fake-codec.webm"; then echo "FAIL: incompatible WebM codec accepted"; exit 1; fi
# No audio/video stream should be accepted without an actual video track.
ffmpeg -hide_banner -loglevel error -f lavfi -i sine=frequency=440:duration=2 -c:a aac -y "$work/audio-only.mp4"
if python3 tests/video/server_validate.py "$work/audio-only.mp4"; then echo "FAIL: audio-only accepted"; exit 1; fi
echo 'PASS: isolated ffprobe duration, codec, video stream, spoofed/malformed/oversize reject'
