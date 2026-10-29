# Poker ID 初回リリースv1（公開はNO-GO）
既存32項目台帳を削除・変更せず、別の初回公開ゲートを追加する。全機能完成率と初回公開可否を混同しない。

候補：認証、通常タイムライン/投稿、画像、コメント/返信、いいね、フォロー、検索、プロフィール、通知、DM。
延期：TDAクイズ/条文検索（公式350問の根拠未証明）、36動物診断/共有（classifier等未証明）、動画/高度分析/ツール/実績/カード/追加機能、poll（従来NO-GO）。既存コード・データを削除しない。PR2/123/GTOを変更しない。

機械可読の対象・延期・12必須条件は FIRST_RELEASE_V1.json。PASSは当該条件の証拠だけを指し、他条件や公開承認に波及しない。UNKNOWN/BLOCKED/欠落は公開拒否。
既存台帳のraw Git blobと32行を別ゲートで検証。初回ゲートの分母は12固定。公式TDA/分類妥当性は偽のPASSにせず、完全な隔離が実証できればSNS初回公開の必須内容から分離する。

初回用入口 first-release.html と vite.first-release.config.ts は通常App/ビルドと別の候補成果物。通常App、package scripts、既存381保護テストは変更しない。
正規の公開用buildコマンド：node scripts/build-first-release.mjs
安全条件未達なら終了コード2でbuild前に停止。node scripts/first-release-gate.mjs はJSONレポート、--check は必須条件未達を非0にする。
CIの候補コンパイル：node node_modules/vite/bin/vite.js build --config vite.first-release.config.ts
これは候補の構文・artifact確認であり公開許可ではない。公開設定/Vercel/本番DBは操作しない。

FirstReleaseApp は公開可否が未達の間、core候補も準備中表示にし、実コンポーネントをimport/mountしない。延期/未知URLは対象外表示。候補メニューに延期導線を出さない。元Appは開発用に保持するが、通常artifactを初回リリースとして誤って公開しない運用検証は別必須。
延期ルートを閉じても、既存投稿/プロフィール埋込、外部share/OG、直接RPC/REST、キャッシュ、旧クライアントを遮断した証明にはならない。nested_and_api_deferral/privacy はこの証拠が揃うまでBLOCKED。特にPR2 api/share.ts は未知重複のため変更しない。
正式auth/RLS/Storage/所有者認可・アカウント切替・モバイルE2E・rollback/reviewを、承認済み隔離環境で完了させるまでNO-GO。ローカル容量/WIP/SQLiteは触らない。

## 実行証拠と判定
旧入口 c89cbc142ed293aa79aa0516d036bc0529dd7214 / CI40834336947：固定ブラウザ30件0PASS/30FAIL、単体5PASS。
専用入口へ切替後、同一30件30PASS/0FAIL。実コンポーネントはfixtureに置換した直接URL/遷移/viewport QAであり、実認証SNS E2Eではない。
成果物固定3件は3ec670a2086f2f943d4fd89ab4e05e935bf7359e /40835986298で1PASS/2FAIL（index.html欠落）。6b860b5844dfc656799c8ac9a4d363ed17cd0c33 /40836608463で3PASS、単体5・ブラウザ30もPASS。
HTMLの確定はwriteBundleで新規dist-first-release内だけに限定し、既存indexや想定外出力先があれば拒否する。通常App/32台帳/既存SQLを改変しない。

初回ゲート4/12：scope・legacy_ledger_preserved・deferred_ui・regression_buildの証拠あり。残る8条件はBLOCKED。4/12は機能完成率/公開承認ではない。
regression_buildはSelected381/現行538実行・通常build/lint・候補build/artifact条件を指す。PR全体CIと同義ではない。
別の既存Poll40836608432では未変更の延期TDA fixtureが2500msでclick/gotoタイムアウト。Selectedの同一ソース反復はPASS、ブラウザbuildは.47対.0と異なる。原因UNKNOWN、assertion/期限は緩和せず、除外した事実や成功再試行を根本解決としない。
最終保存HEADのCIはPR125の最新チェックポイントで照合する。

次工程は、SNSの正式schema/grants/RLS/Storageと実認証隔離環境の受領、PlayerSearch実差分の回収、投稿/プロフィール内診断・pollと直接RPC/共有APIを含む延期機能隔離、実利用E2E/rollback/review。API/shareのPR2は勝手に統合・変更しない。
隔離QAでcoreを検証する場合も、テスト専用構成と公開artifactを区別し、正式な公開入口のOFFや既存安全条件を無断解除しない。通常buildを初回候補と誤公開しないことも必須review条件。

### 候補artifactの追加確認
preview.test.mjs は生成済みindex.htmlをVite previewで配信し、コンポーネントをmockせずに390/1280pxでTDA・診断・timelineの6経路を確認する。閉じた入口では外部通信/データAPI呼出しやpageerrorを許可しない。これはOFF状態のartifact確認であり、認証後SNS E2Eとは別。
ローカルで確認可能になった場合も、通常dev入口ではなく候補build/previewを使い、旧workspaceを壊さない。Vercelや実DBへ接続するテストには置き換えない。
