# Poker ID｜本番反映待ち・リリース台帳

更新日：2026-10-20（Codex読み取り専用監査結果を反映）
管理場所：専用基盤ブランチ `chore/autonomous-dev-foundation-20261020` のみ。本番ブランチには未反映。

## 判定方法
- **差分あり**：GitHub `main...対象ブランチ` 比較で独自コミット・変更ファイルあり。ただし統合済みPRのコミット履歴やcherry-pick等でもaheadが残るため、**本番未統合の証明ではない**。PR状態・tree一致・main実装を優先する。
- **QA未確認**：テスト完了を証明する最新のテストログ、対象コミット、プレビューと環境の一致を未確認。実装失敗とは限らない。
- **本番反映済みの一部あり**：mainに関連ファイルがある。全機能が本番で利用可能とは断定しない。
- 本台帳では **QA合格・即マージ可能** と認定できた機能はゼロ。これはQAが必ず失敗という意味ではない。
- 2026-10-20 Codex監査によると PR #1/#3/#6/#7 は **mainマージ済み**。ただし本番配信・実機QA・DB状況は未確認。監査報告に記載された統合SHAとGit tree一致を根拠とし、デプロイ検証とは区別する。
- VercelのデプロイがREADYでも、mainとの同一性・DB移行・実機QA合格を証明しない。

## 機能別バックログ（2026-10-20 Codex追加監査で訂正）

| 優先 | 機能 | ブランチ・PR | main統合 | QA / 本番判定 | 次の確認 |
| --- | --- | --- | --- | --- | --- |
| P0 | F03通知・セキュリティ等 | `fix/p0-security-audit-20261018` | 未統合、大規模差分（main比ahead 89 / behind 2） | 旧QAにFAILあり、最新修正後の解消証拠は未確認 | 安全な選択統合・再試験・DB権限確認 |
| P0 | F03選択的統合テスト | `test/f03-isolated-integration-20261020`, HEAD `cb31df80…` | 未統合（main比ahead **6** / behind 0） | 分離候補、機能QA・テストログ未確認 | 6コミット・5ファイルの内容と外部通信なしテスト |
| P1 | アンケート・質問箱 | `feature/timeline-polls-questions-20261017`, PR [#4](https://github.com/kyoma1015/poker-sns/pull/4) | **未統合、draft** | 匿名性・権限・締切通知・本番SQLの適用状況が未確認 | 実機QAとRLS/RPC/SQL計画 |
| P1 | プレイヤー診断・QA | `fix/player-type-qa-phase1-20261019`, HEAD `d494b05…` | 未統合 | 旧QA BLOCKED。36動物・保存/公開/画像の最新実機QA未確認 | 未完了QAの移管と実施 |
| P1 | プレイヤー診断・監査 | `fix/player-type-audit-phase1-20261019`, PR [#5](https://github.com/kyoma1015/poker-sns/pull/5) | **未統合、draft** | ビルド・実機QA未実施とのPR記録 | QAブランチとの競合、設問・助言妥当性 |
| 既統合/QA待ち | TDAログイン案内 | PR [#6](https://github.com/kyoma1015/poker-sns/pull/6), `fix/tda-quiz-login-guidance-20261019` | **マージ済み**（Codex監査） | 問題品質・ログイン実機回帰QAは未確認 | 対象コミット・本番配信・UI/認証動作 |
| 既統合/QA待ち | TDAボタン配色 | PR [#7](https://github.com/kyoma1015/poker-sns/pull/7), `fix/tda-login-button-dark-20261019` | **マージ済み**（Codex監査、tree一致） | 本番表示・hover/focus回帰QA未確認 | 実機確認 |
| 既統合/QA待ち | カード公開・縦型OG | PR [#3](https://github.com/kyoma1015/poker-sns/pull/3), `feature/og-vertical-card` | **マージ済み**、統合SHA `7bc1df9…`（Codex監査、tree一致） | Storage/DBと非公開時の他者閲覧QA未確認 | 本番でのアクセス制御・生成・保存・共有QA |
| 残存旧PR | Poker IDカード試作 | PR [#2](https://github.com/kyoma1015/poker-sns/pull/2), `feature/poker-id-card` | PRはdraftのまま。**カード機能の後続版はmainに統合済み** | 古い差分を未リリース新機能として計上しない | PR #3との差分整理と旧PRの扱い |
| 既統合/QA待ち | リングゲーム名称変更 | PR [#1](https://github.com/kyoma1015/poker-sns/pull/1), `rename-amusement-to-ring-game` | **マージ済み**、統合SHA `c3fe008…`（Codex監査、tree一致） | 作成/編集/共有の実機QA未確認 | 本番動作確認 |
| 基盤 | 自律開発・進捗・CI | PR [#8](https://github.com/kyoma1015/poker-sns/pull/8), `chore/autonomous-dev-foundation-20261020` | **未統合、draft** | `7cb7bc3…`でnpm ci / build / lint成功、ビルド・lint・npm監査警告あり | オーナーレビューと継続的自動実行の設計 |

**注記：** main統合済みでもVercel本番配信済み・DBマイグレーション適用済み・機能QA PASSとは断定しない。Codex調査基準 main SHA `f8890b6ec11d30676c55dc7dc8801f1da8549d28`。

## 主要な競合リスク
1. `src/Timeline.tsx`：アンケート、F03、リング名称変更。
2. `src/PlayerTypeDiagnosis.tsx`：診断2ブランチ、F03。
3. `src/TDA.tsx`：TDA2ブランチ。
4. `src/App.tsx`：F03、カード系、リング名称変更、F03統合テスト。
5. `src/PlayerProfile.tsx`：F03、カード系、リング名称変更、F03統合テスト。
6. `api/share.ts` と `vercel.json`：カード系、F03、リング名称変更の変更を照合。
7. `sql/*.sql`：PRマージのみでは本番DBに自動適用されない。オーナー承認の別手順が必要。

## 確認が終わっていないもの
- 各ブランチの実機QA・独立QAの正確なPASS/FAIL/BLOCKEDと対象コミット
- PRの最新状態、Vercelプレビューの該当コミットへの紐付け
- 本番DBにすでに適用済みのSQLやRLSの正確な状態
- 別リポジトリ/ZIPにある可能性の高いGTOエンジン成果物
- 開発ブランチに残っていても他コミットで実質取り込み済みの差分（cherry-pick）の確認

## 次の作業キュー
1. F03部分統合テスト（ahead 6）のCI、差分内容、セキュリティ影響を独立確認。安全性が最優先。
2. アンケート・質問箱のQA証拠、SQL適用状況、締切通知を照合する。QA不足ならQA用タスクを作る。
3. TDAのPR #6/#7はmain統合済み。二重取り込みはせず本番配信・回帰QAを確認。
4. 診断の2ブランチを比較し、既存BLOCKED項目の消化。
5. カードPR #3・名称変更PR #1はmain統合済み。未確認QAを進め、旧カードPR #2は差分整理。
6. 各候補を `実装中 / QA中 / QA合格・承認待ち / 本番反映済み・確認済み` の状態で更新する。

## リリースゲート
1. 変更対象と依存するSQLをすべて列挙
2. プレビュー/ビルド/自動テスト/必要なブラウザQAの証拠を記録
3. mainとの競合解消後に改めてCIを実行
4. 本番DB変更があればSQLを別途作成し明示承認を得る
5. 本番マージ・デプロイも明示承認まで実行しない
