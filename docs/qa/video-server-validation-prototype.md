# Video server validation prototype — NOT DEPLOYED
`tests/video/server_validate.py` uses ffprobe on an isolated trusted server and rejects empty, >20MiB, malformed, non-video, spoofed containers and >30-second media.
CI generates genuine 2s and 31s MP4 videos and runs positive/negative checks.
This is **not** a Supabase Edge Function, is **not** connected to upload/publish and does not establish server-side enforcement for real posts.
Production design must stage uploads privately, validate server-side before a privileged finalization, prevent clients from bypassing finalization, and reclaim rejected/orphaned uploads.
The current client publication block MUST remain.
Storage API and signed-URL E2E have not been run.
