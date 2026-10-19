# Poker ID — 旧8チャットからCodexへの引き継ぎ手順

更新日: 2026-10-20

## 基本原則
- 既存の8チャットは**引き継ぎが確認されるまで削除・終了しない**。新規開発指示だけ一時停止する。
- GitHubのブランチ・コミット・PR・保存済みテストは参照可能だが、旧チャット内の発言・未アップロードZIP・一時ブラウザでのQA状態は自動で取り込まれない。
- ワークスペースの初期ブランチは `work` のことがある。**毎回 `git branch --show-current`、`git rev-parse HEAD` で一致を確認**し、必要なら読み取り専用の一時作業ツリーで対象ブランチをチェックアウトする。
- `docs/progress/RELEASE_BACKLOG.md` の「差分あり」は「QA合格」でも「本番未デプロイ確定」でもない。QA証拠と対象SHA、mainの状態、既存DBの適用状況で検証する。
- 最初の棚卸しは読み取り専用とする。いかなる本番変更、Supabaseへの接続・書込、PRのマージ、公開デプロイもしない。

## 作業系列
| 系列 | 所在候補 | 引き継ぎ確認 |
| --- | --- | --- |
| A監査・セキュリティ・UI | `fix/p0-security-audit-20261018`, `test/f03-isolated-integration-20261020`, 旧A Work/チャット | 残ったFAIL/BLOCKED、F03 RPC/通知と本番差分、安全な部分統合計画 |
| B TDAクイズ | `fix/tda-quiz-login-guidance-20261019`, `fix/tda-login-button-dark-20261019`, 旧B Work/チャット | クイズデータと日本語監査、認証案内、結果画面、QA |
| C GTO | 旧C Work/チャットのZIP・ソース・計測ログ（GitHubの所在は未確認） | G11以降の最終ZIP、SHA、checkpoint、OpenSpielテスト、計算精度・性能、次のG段階 |
| D診断 | `fix/player-type-audit-phase1-20261019`, `fix/player-type-qa-phase1-20261019`, 旧D Work/チャット | 50問、36動物、実機QA未完了とSQL/画像保存、L01改稿資料 |
| 横断プロダクト | `feature/timeline-polls-questions-20261017`, `feature/poker-id-card`, `feature/og-vertical-card`, `rename-amusement-to-ring-game` | アンケート・質問箱・カード・OG・名称変更の機能別QA証拠とDB依存 |

## 各系列の引き継ぎ必須項目
1. **最新実装**：リポジトリ、ブランチ、HEADのコミット、PR、差分ファイル、ZIPの保存先。
2. **完了確認**：どのSHA、どの環境・テスト・日付で PASS/CONDITIONAL PASS を確認したか。
3. **未完了**：FAIL/BLOCKED、未実施ブラウザQA、外部サービス制限、原因と再開位置。
4. **依存関係**：DB migration、RLS、Supabase関数、Vercel Preview、環境変数、別ブランチ。
5. **次の一手**：次に安全に実行できる具体的タスク（変更予定ファイル、完了基準）。
6. **オーナー承認**：本番反映、DB適用、費用、重要仕様など、まだ許可されていない判断。
7. **証拠が見つからない項目は「不明」**。過去チャット内容を推測してPASSにしない。

## 移行ゲート
- Gate 0: Codex CLI/クラウドのリポジトリ読み取り、npm ci / build / lint → CONDITIONAL PASS（2026-10-20、ビルドとLintに警告あり）。
- Gate 1: GitHub内で証明できる5系列の実装・テスト・未完了事項を読み取り専用で整理。
- Gate 2: 旧8チャットにのみ存在する結果を成果物として保存（とくにGTO ZIPとDのQAログ）。
- Gate 3: 小さな独立修正1件をCodexの専用ブランチ→テスト→ドラフトPRまで試運転。mainは変更しない。
- Gate 4: 各系列で引き継ぎ内容とPR/テストが照合できたことを確認してから旧チャットを停止。
- Gate 5: 自動実行のトリガー、同時実行・共有ファイルの排他、停止条件、コスト上限、承認ゲートを実装。単にCodex環境を公開しただけでは常時自動化にならない。

## 直近の読み取り専用Codexタスク
対象：`chore/autonomous-dev-foundation-20261020`。 `AGENTS.md`, `docs/progress/RELEASE_BACKLOG.md`, 本書を読む。
GitHub上の各既知ブランチのHEADとmain差分、存在するQA証跡を調べる。
各系列を `実装が存在 / QA証拠あり / QA不足 / 外部資料待ち / 本番承認待ち` で評価し、証拠URLとSHAを一覧で返す。
未アップロード成果物があれば必須のファイル名と用途を明記する。
今回は**読み取りのみ。ソース編集、コミット、PR、Supabase接続、Vercelデプロイを禁止**。
