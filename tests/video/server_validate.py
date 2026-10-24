#!/usr/bin/env python3
"""Isolated, trusted-server media validation prototype. NOT wired to production."""
import json
import math
import os
import subprocess
import sys

MAX_BYTES = 20 * 1024 * 1024
MAX_SECONDS = 30.0
MIME_BY_EXT = {".mp4": "video/mp4", ".webm": "video/webm"}

def verify(path: str) -> dict:
    ext = os.path.splitext(path)[1].lower()
    if ext not in MIME_BY_EXT:
        raise ValueError("unsupported extension")
    size = os.path.getsize(path)
    if size <= 0 or size > MAX_BYTES:
        raise ValueError("file exceeds 20 MiB or is empty")
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams",
         "-of", "json", path],
        check=True, capture_output=True, text=True, timeout=20,
    )
    meta = json.loads(result.stdout)
    streams = meta.get("streams") or []
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    if len(video_streams) != 1:
        raise ValueError("expected exactly one video stream")
    allowed_video_codecs = {".mp4": {"h264", "hevc", "av1"},
                            ".webm": {"vp8", "vp9", "av1"}}
    if video_streams[0].get("codec_name") not in allowed_video_codecs[ext]:
        raise ValueError("unsupported video codec for container")
    if not isinstance(video_streams[0].get("width"), int) or not isinstance(video_streams[0].get("height"), int):
        raise ValueError("missing video dimensions")
    if not 1 <= video_streams[0]["width"] <= 4096 or not 1 <= video_streams[0]["height"] <= 4096:
        raise ValueError("video dimensions out of range")
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    if len(audio_streams) > 1:
        raise ValueError("multiple audio streams")
    allowed_audio_codecs = {".mp4": {"aac", "mp3", "opus"},
                            ".webm": {"opus", "vorbis"}}
    if audio_streams and audio_streams[0].get("codec_name") not in allowed_audio_codecs[ext]:
        raise ValueError("unsupported audio codec for container")
    if any(stream.get("codec_type") not in ("video", "audio") for stream in streams):
        raise ValueError("unexpected auxiliary stream")
    fmt = (meta.get("format") or {}).get("format_name", "")
    if ext == ".mp4" and not any(x in fmt.split(",") for x in ("mp4", "mov")):
        raise ValueError("not an MP4 container")
    if ext == ".webm" and "matroska" not in fmt:
        raise ValueError("not a WebM container")
    durations = [float(v) for v in
                 [meta.get("format", {}).get("duration")] +
                 [s.get("duration") for s in streams]
                 if v is not None]
    if not durations or not all(math.isfinite(v) and v > 0 for v in durations):
        raise ValueError("missing or invalid duration")
    duration = max(durations)
    if duration > MAX_SECONDS:
        raise ValueError("video exceeds 30 seconds")
    return {"duration": duration, "size": size, "container": ext}

if __name__ == "__main__":
    try:
        print(json.dumps(verify(sys.argv[1])))
    except (ValueError, OSError, subprocess.SubprocessError, json.JSONDecodeError, IndexError) as error:
        print(f"REJECT: {error}", file=sys.stderr)
        sys.exit(1)
