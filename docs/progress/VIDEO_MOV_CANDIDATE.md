# MOV conversion candidate — 2026-10-30

Base main: 0e85cb2981b6290247eded54b695ad43d2e00338. Production remains testplayer-only; this candidate is not production approval.

Acceptance before deployment: local MOV converted to bounded H264 with AAC (preferred) or Opus MP4, actual decoded audio retained, cancellation/unmount/account-switch never restores a stale attachment, no upload before normal validation. Original MOV is never uploaded. Existing server SHA256/ffprobe/HMAC/owner/allowlist checks are unchanged. No database migration or new function is required for this client conversion.

The converter uses native MediaRecorder MP4 support, canvas frames and decoded Web Audio. Unsupported codecs/devices, >20MiB input, >30s input, corrupt media, backgrounding, cancellation, timeout and >20MiB output fail closed. UI explains offline iPhone Encode Media fallback. Conversion runs in real time and requires keeping the page visible; output must be reviewed before posting. Existing oversized compression stays disabled.

New workflow tests changed client build/lint and real Chromium MOV/H264 with AAC (preferred) or Opus conversion with ffprobe and decoded PCM energy (not only track presence), abort, malformed and oversized input, and zero external requests. Physical iPhone Safari and HDR/HEVC source compatibility remain unproven until device testing. A browser CI pass is not Safari evidence.

General rollout still requires a separately reviewed server+DB authorization change. Do not simply clear the allowlists or trust user_metadata. Maintain emergency DB settings.enabled=false and server VIDEO_SERVER_ENABLED=false rollback, owner hide, retained rows/files, and prior deployment SHA. Full backup/restore is still incomplete.
