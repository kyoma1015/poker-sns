# Video posting and published-transfer recovery

On the reported iPhone Preview, MOV conversion and audio playback passed. The deployment matches bb246b2ecac80c8f17768e66513017c645a6bce6. Vercel currently lists the client and server video flags for Production only. A disabled HTML button does not invoke the handler. Both composers now label and visually dim the blocked state without changing the publication gates.

Production recovery inspection uses the existing owner JWT, posts RLS, immutable generation RPC and bounded Storage read. It returns a proof only for an existing visible owner post whose recorded SHA256 and generation match the actual bytes. The client compares the proof with its current journal and preserves the original transfer and pending records in session storage before replacing their active status. Unpublished or ambiguous transfers remain blocked. No resend, delete or schema migration is involved.

Physical iPhone submit and protected Preview write validation are separate release evidence.

PR #134 Storage HTTP run 45855837353 reached Chromium but the isolated finalize handler returned 503 for published-transfer inspection. The follow-up runs the same proof against loopback Supabase with the injected isolated adapter. The browser harness drops the socket after commit and before sending headers, and checks for one publication, no second reservation and a successful read-only proof. CI results are tracked on the PR.
