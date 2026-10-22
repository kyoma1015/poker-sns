# Poker ID | 通常開発ボード
更新: 2026-10-20 JST

通常開発再開: YES（開発ブランチ限定）。本番リリース: BLOCKED。
統合ブランチ: codex/integration-poll-only-20261020。
旧8チャットを毎回参照せず、本リポジトリの実装・テスト・本ボードから継続する。未転送資料を受領済みと扱わない。

| 系列 | 保存済みの再開位置 | 次の作業と完了条件 |
|---|---|---|
| B | PR #11、認証回帰11件 | 公式問題原文の照合、認証あり実機QA。問題の正確性は未確認 |
| D | PR #10、診断回帰40件 | 隔離環境で結果保存・URL・PNG・36分類QA。L01は適用しない |
| A | PR #9、F03選択5ファイル・回帰11件 | 隔離DBでイベント真正性・冪等性・旧INSERT権限を確認。権限変更は別承認 |
| SNS | 修正版PR #12、poll-only・回帰27件・モックブラウザ5件 | 隔離DBで匿名性/締切/通知1回を確認。質問箱は公開対象外 |
| C | handoff/gtoに3ソルバーと関連ソース、ハッシュ・SQLite25件 | C_GTO.md参照。vendor依存転送後に無改変ビルド、checkpoint再開は別ゲート |

詳細: INTEGRATION_VERIFICATION_20261020.md、各系列の進捗ファイル、docs/qa/integration-20261020/。
本番マージ・デプロイ・本番DB変更・課金は禁止。CI PASSは本番DBや実機QAの完了証明ではない。


## Issue22 continuation — 2026-10-21
Latest evidence and restart contract: docs/workers/ISSUE22_RESTART_STATE_20261021.md (PR34). A poll PR31 isolatedDB56PASS/client30/mobile5, production gates remain; B PR32 saved-result integrity; C PR33 synthetic rank7; D PR35 doubleclick; PR34 reviewed replenishment and bounded recovery. Each has published CI SUCCESS at code SHA. Formal host stop/reopen/resume plus real source implementation verified for simulated quota; future scheduled autonomous completion remains unverified. Do not treat old table above as latest runtime evidence.


## PR overlap resolved — 2026-10-21
Current implementation/restart evidence: PR38 docs/workers/RECONCILED_RESTART_20261021.md. A37/B41/C39/D40 and overlap38 implemented/CI passed. New exact Gitproof gates permit inherited samefile changes, unknown overlaps still block. B19 reviewed normalmerge preservedsource. Next B/C/D fixed inputs each READY on fresh34PRsnapshot, awaiting bounded scheduled/host dispatch. No main/production release.

## Ordinary scheduled source continuation — 2026-10-21 17:05 UTC
C ready-next completed as PR57 c73b57d156e3c1aae24e10565787df4d73b1c3a8 (14+40PASS); B as PR59 35502ff3af55e58c5ffb518fe7d1a2d7db631e64 (browser9/unit138/build/lintPASS); D as PR60 93d9948f8f829432fa66c5aafd294bf8924421fa (browser6/unit96/build/lintPASS). Do not rerun these IDs or edit immutable descriptors. Evidence: PR38 ordinary-scheduled-source-chain.json and RECONCILED_RESTART. Two recurring prompt arrivals observed; independent coldstart/daemon and provider runID remain unverified. Original durable4task hashes retained. Next executable descriptors require new fixed failing acceptance and review; none falsely marked ready. Other work merged poll PR31, PR42–56 and PR58 into main; current main release gate still NO-GO. This worker did not merge/deploy/connect production or change finite schedule.

## Scheduled continuation — 2026-10-21 23:05 UTC
New actual source: C PR61 b6456dce6e8f468448f2daedc8850dce6d7d76ff (22+40PASS/CI39690270215), B PR62 be0fd9197bb17c0ff6de15ec9527a12ff49241c2 (browser16/unit138/build/lintPASS/CI39690895245). A37/D60 unchanged. Next C issue22-c-chip-oracle-types-v1 has new input7fa1ffd5de8a7bb0479f4f5348445782326cde8e, fixed28 FAIL/protected5/READY-on37PRsnapshot; NOT source-implemented or dispatched. Read PR38 docs/workers/SCHEDULED_CONTINUATION_20261022.md and RECONCILED_RESTART. Later scheduled prompt and fresh gates required. Original state/finite schedule retained; no main/production changes.

## Explicit follow-up — 2026-10-22
C v1 BLOCKED: prior coordinator descriptor mistakenly treated refund as scalar; original17/refund vector contradict it. Old fixed28/5ERROR and worktree/spec retained. Corrective immutable v2 input115adb8a6ec7aff591aaf90d479a1eb205c1d24b -> Draft PR66 b492f8c7730cb5ebb66beee909ba2526dcb7cc85, fixed29/oldGTO40PASS,CI39711822875SUCCESS. Only settlement.py source changed; one corrective retry. B62/D60 source maintained; official350/36-animal semantic evidence remains incomplete. Main now includes external64/65 at3ff2c03bddcf74c252f2533769f79ccc85dba1fe; this worker did not merge. PR13/12/8/2 conflict with main; releaseNO-GO and realbackup/restore awaiting trusted alternative environment. Details: PR38 docs/workers/ISSUE22_FOLLOWUP_20261022.md. This was explicit user execution, not scheduler/coldstart proof.

## Issue22 verification update — 2026-10-22
See [evidence ledger](../workers/ISSUE22_VERIFICATION_20261022.md). New isolated source Draft69 SQLite init and Draft70 exact toy BR metrics have successful CI. PR66 fixed input passes but inherited full branch conflicts with current main in seven files. B350 immutable source/review, D36 semantic classification, originalG11 compatibility/poker convergence and poll production release remain BLOCKED; no main merge or production operation.
