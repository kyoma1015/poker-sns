# Poker ID 自動化 稼働確認台帳

更新日: 2026-10-20

| 機能 | 状態 | 根拠 |
| --- | --- | --- |
| TypeScript / ViteビルドとLint | PRブランチでPASS | GitHub Actions Quality Check run 39289320424 |
| 開発ライン進捗記録 | 作成済み・一部照合済み | docs/progress/MASTER.md |
| Issue自動分類 | PRで設定追加・未稼働 | .github/workflows/issue-triage.yml |
| Issueから自動コード修正 | 未実装 | 実行エージェント未接続 |
| 自動PR作成・AI反復修正 | 未実装 | 実行エージェント未接続 |
| 本番デプロイ承認制 | 運用ルールを記載済み、強制設定未確認 | docs/progress/AGENT_OPERATING_RULES.md |

## 今回導入したIssue自動分類
- Issueタイトルが [A] [B] [C] [D] で始まるものだけ対応し、担当ラインのラベルを付ける。
- タイトル変更に合わせて古い担当ラインのラベルだけを外す。
- Issue本文をコマンドとして実行しない。PR、ソースコード、Supabase、本番環境を変更しない。
- GitHub Actionsのissuesイベントはデフォルトブランチにworkflowが存在して初めて動作するため、PR #8がドラフトの間は**未稼働**。
- GitHub Actionsの実行枠、リポジトリ設定、branch protectionは別途確認が必要。

## 運用注意
この自動分類はAIエージェントではない。リポジトリ上のファイルを更新しただけでWorkが勝手に実行されることはない。本番DBやmainへのマージには引き続きオーナー承認が必要。
