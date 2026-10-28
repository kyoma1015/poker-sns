# Cloud HTTP implementation checkpoint
Dedicated finalize dispatch now uses server/video-cloud-http.mjs inside the existing Vercel function. Request JWT getUser plus allowlist; reservation manifest; owner-bound private Storage download limited to20MiB; actual ffprobe and SHA256; authoritative manifest/generation recheck; fresh JWT; random nonce and independent VIDEO_CLOUD_TEST_HMAC_HEX/ID; atomic cloud publish RPC.
Dedicated media reuses existing bounded, reauthenticated owner/RLS playback. Client dedicated flag activates existing video UI without changing production VITE_VIDEO_SERVER_ENABLED. Upload passes manifest and content to reservation.
New video_cloud_state RPC is private-owner/allowlist/expiry scoped. Must apply only to dedicated test project after earlier migrations.
Syntax checked only locally. Real dedicated HTTP and Chromium E2E are not yet implemented; do not provision cloud or claim complete. No cloud secrets/provisioning performed.
