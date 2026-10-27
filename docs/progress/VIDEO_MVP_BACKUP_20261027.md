# Video MVP — Work-only backup capability audit
Updated: 2026-10-27 JST. Start HEAD b8efe9ebe66cbfbf1a79916a3ff634d0567fefd4. PR #123.

## Acceptance
No user VS Code/terminal/CLI/manual backup steps. No production private bytes in GitHub, chat, CI or public storage. Release requires actual complete DB + Storage export and independent isolated restore. No extra cost or destructive changes.

## Confirmed capability and blocker
All three apps have Allow all actions. GitHub collaborator permission admin; source writes and CI reads work.
Supabase SQL session: postgres, rolsuper=false, rolbypassrls=true, pg_read_server_files=false, pg_execute_server_program=false. 4 buckets / 7 objects (counts only); existing branches empty.
Exposed Supabase methods have no DB dump stream, Storage object byte download, or confidential credential delegation to the runner. SQL results are not a safe bulk backup channel and do not contain Storage bytes.
Plugin search found installed Supabase but no additional relevant export connector. No existing approved no-cost isolated restore target is available.
No actual DB/Storage backup or restore was performed. Do not repeat these probes absent a changed capability surface. No SQL secret extraction, Vercel secret extraction, COPY PROGRAM, public URL or production Edge Function export workaround.
No user manual operation is requested; Work-only completion remains blocked on provider-supported confidential export plus no-cost isolated restore capability.

## Vercel evidence
Official https://vercel.com/docs/limits: Hobby 100 deployments / 86400 seconds, owner-scoped. Exact reset epoch UNKNOWN.
A single Preview API request for start HEAD was accepted: dpl_E5dKnb6QYjWy4Ppa7cTS9xfrHo27, https://poker-3kbfx48ln-poker-sns.vercel.app . Last observed BUILDING; final outcome must be checked. No upgrade or production deploy.

## Code and local verification
Manifest v2 hashes bucket configuration and inventory, checks project/version, reconciles bucket/object counts and rejects unsafe filesystem entries. Legacy manifests are rejected.
python3 -m py_compile scripts/video_private_storage_export.py PASS.
python3 -m unittest discover -s tests/video -p test_private_storage_export.py -v PASS (8 synthetic tests).
No full local npm build/lint; repository-wide CI is required. Synthetic checksums prove local consistency, not remote restoration or attacker-resistant authenticity. Before/after listing is not a transactional snapshot.

## Production security audit and impact
Security advisors ran read-only. Existing warnings include mutable search_path, executable SECURITY DEFINER functions and disabled leaked-password protection; INFO includes RLS without policies. Findings need contextual review, not indiscriminate production permission changes.
No production DB/Storage/schema/key/config write, main merge, production deploy or production browser QA. Video gates remain disabled.
