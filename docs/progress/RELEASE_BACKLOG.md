# Poker ID｜本番反映待ち・リリース台帳

更新日：2026-10-20
管理場所：専用基盤ブランチ `chore/autonomous-dev-foundation-20261020` のみ。本番ブランチには未反映。

## 判定方法
- **差分あり**：GitHub `main...対象ブランチ` 比較で独自コミット・変更ファイルあり。
- **QA未確認**：テスト完了を証明する最新のテストログ、対象コミット、プレビューと環境の一致を未確認。実装失敗とは限らない。
- **本番反映済みの一部あり**：mainに関連ファイルがある。全機能が本番で利用可能とは断定しない。
- 本台帳では **QA合格・即マージ可能** と認定できた機能はゼロ。これはQAが必ず失敗という意味ではない。
- VercelのデプロイがREADYでも、mainとの同一性・DB移行・実機QA合格を証明しない。

## 機能別バックログ（2026-10-20 GitHub比較）

| 優先 | 機能 | ブランチ | mainとの差分 | QA / 本番判定 | 次の確認 |
| --- | --- | --- | --- | --- | --- |
| P0 | F03通知・セキュリティ／共有機能等 | `fix/p0-security-audit-20261018` | ahead 89 / behind 2; 20変更ファイル | 大規模未統合・QA判定未照合 | 独立した部分統合案と本番影響、DB変更を確認 |
| P0 | F03選択的統合テスト | `test/f03-isolated-integration-20261020` | ahead 5 / behind 0; 5変更ファイル | テストブランチ、リリース確定ではない | テスト記録とCIを確認し、先行5コミットの内容を監査 |
| P1 | アンケート・質問箱 | `feature/timeline-polls-questions-20261017` | ahead 48 / behind 2; 8変更ファイル | 未統合・QA合格未確認 | 投票/質問/匿名性/締切通知/SQLの安全性と実機QA |
| P1 | TDAログイン案内 | `fix/tda-quiz-login-guidance-20261019` | ahead 2 / behind 2; `src/TDA.tsx` | 未統合・QA合格未確認 | 2修正ブランチを比較し一貫したログイン導線を検証 |
| P1 | TDAログインボタン配色 | `fix/tda-login-button-dark-20261019` | ahead 1 / behind 1; `src/TDA.tsx` | 未統合・QA合格未確認 | 案内変更との重複・回帰テスト |
| P1 | プレイヤー診断・QA | `fix/player-type-qa-phase1-20261019` | ahead 3 / behind 2; 5変更ファイル | 未統合・QA合格未確認 | 50問・36動物・保存/結果/表示の独立QA |
| P1 | プレイヤー診断・監査 | `fix/player-type-audit-phase1-20261019` | ahead 2 / behind 2; `src/PlayerTypeDiagnosis.tsx` | 未統合・QA合格未確認 | QAブランチとの相互差分解消 |
| P2 | Poker IDカード・QR等 | `feature/poker-id-card` | ahead 36 / behind 4; 12変更ファイル | mainにもカード関連コードあり、追加差分は未統合 | 現本番のカードとの機能差分・QA照合 |
| P2 | カード縦型OG画像 | `feature/og-vertical-card` | ahead 44 / behind 4; 14変更ファイル | mainにもカード関連コードあり、追加差分は未統合 | OG/QR/画像エンドポイント・Storage SQL・画像のQA |
| P2 | リングゲーム名称変更 | `rename-amusement-to-ring-game` | ahead 8 / behind 5; 8変更ファイル | 未統合・QA合格未確認 | 表示名統一と記録/編集/共有への影響 |
| 基盤 | 自律開発・進捗・CI | `chore/autonomous-dev-foundation-20261020` | ドラフトPR #8 | main未統合、初期CI合格、後続変更は別途確認 | 変更を限定してレビュー、承認後に導入 |

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
1. F03部分統合テストのCI、差分内容、セキュリティ影響を独立確認。安全性が最優先。
2. アンケート・質問箱のQA証拠、SQL適用状況、締切通知を照合する。QA不足ならQA用タスクを作る。
3. TDAの2ブランチを一つの修正候補にまとめて回帰QA。
4. 診断の2ブランチを比較し、既存BLOCKED項目の消化。
5. カード系・リング名称変更の重複部分を調査。
6. 各候補を `実装中 / QA中 / QA合格・承認待ち / 本番反映済み・確認済み` の状態で更新する。

## リリースゲート
1. 変更対象と依存するSQLをすべて列挙
2. プレビュー/ビルド/自動テスト/必要なブラウザQAの証拠を記録
3. mainとの競合解消後に改めてCIを実行
4. 本番DB変更があればSQLを別途作成し明示承認を得る
5. 本番マージ・デプロイも明示承認まで実行しない
