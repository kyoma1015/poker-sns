# Codex Cloud / GitHub Agent 導入準備

## 現在できたこと
- `AGENTS.md` でコードエージェントの作業規範を明記
- 担当4ラインと進捗ファイルを共通化
- 変更に対する npm ci / TypeScript+Vite build / Oxlint CI
- Issueラベル振分け用ワークフローをPR上に用意（mainにない間は稼働しない）

## まだ行っていないこと
- Codex Cloud環境の作成、GitHubリポジトリの環境接続
- Codex CloudのIssue自動受注・自動実行
- GitHub APIシークレット設定やOpenAI API課金設定
- PR自動修正エージェント常駐、実行コスト監視
- GitHubブランチ保護の設定確認

## 初回試行手順（オーナーの操作が必要）
1. ChatGPTアカウントでCodex Cloudを開く。
2. GitHub連携で `kyoma1015/poker-sns` を選択し、クラウド環境を作成する。
3. 追加のシークレット、プロダクションDB接続、課金設定は行わない。
4. `main` に書き込まない・本番変更禁止・ドラフトPRまでを守る簡単なタスクを1件試す。
5. 結果をCI・実機QA・安全面で評価してから自動起動方式を決める。

## 実行方式の違い
- Codex Cloud: ChatGPTアカウントと連携してクラウドタスクを実施。対象プランの利用上限が適用され、Workと枠を共有する場合がある。
- GitHub Actions + openai/codex-action: APIキー、GitHub Secrets、API使用料金と安全な権限設計が必要。無断で有効化しない。
- GitHub Issue分類: 単純なラベル付与であり、AI実装機能ではない。

## 自動化前チェック
- 外部起動を行うワークフローは信頼できる呼び出し元のみ、最小権限、レート制限、期限、費用上限を設定。
- シークレットをpull_requestの未信頼コードへ渡さない。
- 本番DB操作と本番デプロイを技術的に制限し、PRドラフトとCIで停止。
- 4ラインの衝突を統括してから統合する。
