# Cloud test implementation checkpoint
2026-10-28: existing HEAD ad04a423 had SQL40691532843, Storage40691532795 and Poll40691532777 SUCCESS.
Acceptance before this change: actual finalize (reservation and publication share this entrypoint) and media handlers must reject inconsistent dedicated-cloud configuration before auth/RPC/Storage/ffprobe IO. Test endpoints without explicit configuration must also fail closed.
Connected the target guard to both handlers, added missing-mode detection and declaration types, plus regression checks for the entrypoint ordering.
This is deny-first integration only. It does NOT enable cloud publication. Existing production approval gates and local-only recovery remain unchanged. Client upload/startup integration, allowlisted test identities, minimal cloud SQL, secure random-key provisioning and dedicated Preview site still required.
No cloud SQL/provisioning/keys or production operations performed.
