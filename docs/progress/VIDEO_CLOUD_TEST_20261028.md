# Cloud test implementation checkpoint
Acceptance: reject production endpoints/projects, production deployment targets, privileged clients and release flag reuse before any cloud test IO. Exact test ref hbhyuotzginwysrineyo only.
Added dependency-free fail-closed target guard and adversarial regression tests. This is a prerequisite helper only; it is NOT wired into handlers and does not enable cloud publication.
Still required: allowlisted test identities, minimal reviewed migration with direct post INSERT denied, immutable private Storage and atomic nonce/HMAC publication, secure independent random key provisioning, dedicated Preview client and API integration, real isolated regression and cloud E2E.
No SQL/cloud provisioning or secret generation performed at this checkpoint. Production remains disabled. Never apply local bootstrap QA policies or fixed keys to cloud.
