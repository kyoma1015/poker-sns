# Poker ID | 統合検証・引き継ぎ完了判定
2026-10-20 JST。通常開発: YES（専用ブランチ）。総合 CONDITIONAL PASS。本番リリース BLOCKED。

## 基準・取り込み順序と正本
main: f8890b6ec11d30676c55dc7dc8801f1da8549d28。
引き継ぎ資料: chore/codex-handoff-artifacts-20261020 @ 8509484bf9186534ca10694eb62aba7075395aee。
実行ブランチ: codex/integration-poll-only-20261020。コミットSHAとDraft PRはGitHubの当該HEAD/PRに記録する（文書自身のSHAを埋め込まない）。

| 順番 | PR / 元コミット | 統合内容 |
|---|---|---|
| 1 B | #11 / aed6425d5e70379139f3b35ae66cedffa3a55786 | TDA認証切れと通信障害の区別 |
| 2 D | #10 / 1d8fdfe8e69b645796ff85ac18c8d2b4f026c69f | 診断復帰・リクエスト無効化・50問検証・表示文言 |
| 3 A | #9 / 1451f343521915351cb79678575e4438f13aafa7 | F03選択5ファイル、直接通知INSERTをverified RPCへ |
| 4 SNS | #12 / b8747b414cde39e7c7c244d5c06d9294c68a7e84 | アンケート機能。続くpoll-only修正66cb278a2e4d53c1afa0fa13bb880eadc2a032ecと同等の修正を統合 |

mainから新しいローカルブランチを作り、上記4SHAを順次cherry-pick。Timeline/PostDetailはGitの3-wayで自動統合され、手動競合マーカーは発生しなかった。統合後にF03呼出し・コメント保存IDとアンケートRPCを再検証。whole-fileによるA変更の上書きはしていない。
PR #6/#7はmain済みで二重適用していない。main/本番/Supabaseには変更していない。

## アンケート専用化
受入基準: ホームと下部ナビ作成画面に質問箱経路なし、古いquestionモードでもRPC前に拒否、過去データ/内部コード/SQL保持、匿名投票で氏名を描画しない。
Timelineのモードをnormal/pollに限定。両composerで共通createPollRequestを使い、2–4選択肢・空白/重複/長さ・期限・投票方式を検証する。QuestionThread内部コードは保持するが公開側からマウントしない。既知の質問箱投稿はタイムライン/リポスト・詳細画面から除外する。DB削除はしていない。
匿名結果のvoters/answersを表示前に除外。これはクライアントの保護であり、サーバーの匿名性を証明しない。旧クライアント/直接RPC/他の過去コンテンツ参照経路をDBで遮断する変更はしていない。

## 実行結果と再実行
証拠: docs/qa/integration-20261020/（ログはこのコミット対象のソースで取得）。
- `npm ci --cache /workspace/work/npm-cache --fetch-retries=0 --fetch-timeout=15000`: PASS、179 packages（外部ネットワークを許可した隔離作業環境）。install.log参照。
- `for test_file in tests/*.test.mjs; do node "$test_file" || exit; done`: 89 PASS、0 FAIL（F03 11、診断40、TDA11、poll vote10、poll-only17）。
- `npm run build`: PASS。Vite大チャンク警告あり。
- `npm run lint`: PASS（警告あり、エラー0）。過去からのReact hooks/purity等の警告は未解消、警告を無効化していない。
- `node tests/browser/poll-only.mjs`: Chromium 154.0.8037.57で5 PASS。ローカルの実TSX＋インメモリSupabaseモック。外部HTTP要求を遮断し、実DB/本番認証を使用しない。ホーム記名作成、下部ナビ匿名作成、匿名一覧非表示、記名一覧、旧質問箱カード非表示を検証。実サービスE2Eとは区別する。
- Browser再実行: npm ci後、`CHROMIUM_PATH=/usr/bin/chromium node tests/browser/poll-only.mjs`。CIでは既存の`/usr/bin/google-chrome`を使用。playwright-core 1.64.1はdev dependencyのみ。
- `python handoff/gto/verify_native_solvers.py`: 3ソルバーの実バイト・サイズ・SHA PASS。
- `python handoff/gto/tests/run_backend_tests.py`: ヘッダー/ルール/packed backendの3ハッシュと一時SQLite25件PASS。元build.shも781 bytes/SHA一致。詳細C_GTO.md。
- `npm audit --omit=dev --json --cache /workspace/work/npm-cache`: 検出によりexit 1。production分類の既存high 2（undici/@fastify/busboy）、critical 0。audit-production.json参照。今回のplaywright追加前からロックされている依存。到達可能性と修正の互換性は未監査、リリース前に対応が必要。
- GitHub CIは同じunit/Python/build/lint/browserを実行。統合HEAD bd3996304c1de26b0026ebacf3cb4f31a723286bで全工程SUCCESS: https://github.com/kyoma1015/poker-sns/actions/runs/39370713447 。続く証拠追記コミットのCIも統合PRで確認する。

追加の既存Next Python backend回帰: `python -B handoff/gto/g12_next/g12_p1_live_backend_tests.py` は一時SQLiteのみで9 PASS（gto-next.log）。CIにも追加。GTOのbackend回帰合計は34件で、native solverのテスト件数とは区別する。

## 隔離DB・未完了QA
隔離DB未構成のためBLOCKED。本番DBには接続しなかった。
通知: guest/401/403/42501/22023の非再試行、503/ネットワーク/タイムアウトの上限付き再試行、直接INSERT非使用と保存済みcomment IDをモック/静的テスト。イベント真正性・RLS・冪等性・旧クライアントINSERT権限は未検証。INSERT権限は変更していない。
アンケート: vote requestの匿名/記名一致・期限境界・不正選択・旧questionモード・表示時の個人情報除外を単体/ブラウザで代替。DBの三者（投稿者/投票者/第三者）匿名性、RPC/RLS、履歴/通知の漏洩、1人1票、締切、close通知一回/cronは未検証。
診断: 実認証の保存/URL/PNG/36分類の実機QAは残る。L01 SQLは適用していない。
TDA: 公式問題原文と公開問題の全件照合は未確認。過去SQLを再実行していない。

## 旧PRの整理
#4は旧poll/question混合候補。poll-onlyの#12と本統合PRが後継で、質問箱作成経路を採用しない。
#5の表示上の保証表現修正は#10のavoidSkillGuaranteesで取り込み済み。古い25%ランキング閾値は新QAのfixtureと矛盾するため再導入しない。
#4/#5は後継統合Draft PR #13作成後にsupersededとしてclose済み。ブランチ/履歴/原本は削除しない。#9–#12は系列別のレビュー履歴として維持し、本統合PRと重複マージしない。

## 引き継ぎ終了と通常開発
A/B/D/SNSは本ブランチ、MASTER.md、各系列進捗、保存済みテストを起点に開発を継続できる。旧チャットを毎回確認する作業は不要。ただし未転送の原ZIPや旧チャット原本を廃棄してよいという判定ではない。
GTOは実ソースの現存とPython検証まで移管済み。vendor ZIP 1,588ファイル、G11比較資料、complete checkpointが未受領/未確認で、native build・比較・過去再開はBLOCKED（C_GTO.md）。正本は未選定。
次の開発: 隔離DBの再現可能なschema/seed/権限テストを整備し、上記のserver側ゲートを通す。依存highの到達可能性調査と互換修正を別の小PRで進める。mainへのマージ/本番反映は行わない。
