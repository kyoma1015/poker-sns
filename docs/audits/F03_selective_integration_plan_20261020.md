# F03 production integration plan (audit branch only)

Source: fix/p0-security-audit-20261018
Target later: production main (NOT modified)

Do not merge the entire audit branch: main/audit diverged and contain unrelated feature changes.

## Exactly five files
- src/createVerifiedNotification.ts: add from audit branch, unchanged.
- src/Timeline.tsx: import helper; replace only the like notification direct INSERT with createVerifiedNotification('like', post.id).
- src/PostDetail.tsx: import helper; replace direct INSERTs for like and comment respectively with createVerifiedNotification('like', post.id) and createVerifiedNotification('comment', savedComment.id). The savedComment ID must be used after save succeeds.
- src/PlayerProfile.tsx: import helper; replace only follow notification direct INSERT with createVerifiedNotification('follow', id).
- src/App.tsx: isolate ClientUpdateNotice component and one render in AppLayout; use DOMParser-safe getAttribute src path comparison. Do not replace routing.

## Safeguards
- NEVER overwrite whole TSX files using their audit versions. Preserve all unrelated main features.
- Re-fetch current main and compare exact SHAs before generating merge diff.
- Preview then run independent QA; no unapproved test writes.
- Old production tabs still use direct INSERT; do not revoke INSERT yet.
- A version banner added to new code cannot reach tabs that loaded older code.
- Main merge, production deployment, and any live DB modifications require separate approval.

Status: document only, not an executable patch or production readiness approval.
