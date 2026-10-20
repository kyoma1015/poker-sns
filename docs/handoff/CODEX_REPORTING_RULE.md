# Codex completion report — persistent rule

Scope: Poker ID Codex work on this repository. Apply this reporting format at the end of **every** task, including blocked and read-only tasks.

## Final answer contract

- Emit exactly **one fenced Markdown code block at the end**, containing the complete handoff report in Japanese.
- Put no completion report, status, or additional prose after the block.
- Make the block self-contained so the user can copy it using one Copy action and paste it into ChatGPT.
- Include: task identifier and timestamp (JST), overall verdict (PASS / CONDITIONAL PASS / FAIL / BLOCKED), operations performed, verified facts and evidence, exact repository branch and full commit SHA, changed files (or explicitly 'none'), tests executed and non-executed tests, production / SQL / merge / deploy state, missing artifacts and risks, next steps and acceptance conditions, decisions required from owner.
- Distinguish witnessed facts from prior reports, inferred facts, and UNKNOWN. Distinguish 'artifact hash ledger accessible' from 'original ZIP bytes accessible'. Do not claim GTO recovery on ledger alone.
- Never include secrets or raw credentials in the report.
- If a capability is unavailable, state BLOCKED and give the exact blocker instead of claiming success.

## Operational constraints

This is a presentation rule only, **not** permission to modify production Supabase, run SQL, merge to main, deploy, create paid services, delete artifacts, or change application behavior. Get explicit owner approval for those actions. Do not rewrite past evidence to match newer expectations.

## Minimal report template

```text
# Poker ID | TASK ID | YYYY-MM-DD HH:mm JST
判定：
対象リポジトリ・ブランチ・フルSHA：
実施したこと：
確認した証拠：
変更ファイル・コミット：
テスト結果（未実施も明記）：
本番／DB／mainへの操作：
未完了・リスク：
次の具体的作業・完了条件：
ユーザーへの確認事項：
```
