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

2026-10-23 C: finite actual native training batches and verified exact checkpoint
continuation added in a separate PR20 follow-up. See
`docs/workers/GTO_NATIVE_TRAINING_BATCH_20261023.md`; original G9/G11 and strategy
convergence are still blocked. No autonomous launch or production adoption.
