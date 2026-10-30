# Trusted video finalization core — candidate, not deployed

`tests/video/finalize_core.py` is a **server-only** dependency-injected finalization core. It validates an authenticated UUID and owner-scoped object path, checks ownership using a trusted adapter, verifies downloaded staged bytes using ffprobe, calls a trusted post-insertion adapter, and removes the staged object on validation or insertion failure. Unit tests cover success, invalid duration, DB failure and ownership rejection.

**Critical unresolved integration work:**
- No production HTTP endpoint or Supabase JWT verifier is wired. The authenticated user ID MUST be derived from verified credentials, never a request body.
- No trusted Storage download/ownership or atomic DB post insertion adapters are implemented.
- No durable orphan retry queue or idempotent recovery exists; cleanup errors may leave objects behind.
- No public viewer authorization and playback-signing service exists. A signed URL is a bearer capability; anyone possessing it can access the object until expiry.
- No safe concurrency protection against staged object replacement or simultaneous finalize/delete.
- The client posting block remains mandatory. Do not deploy or enable video publishing.
