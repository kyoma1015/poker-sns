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
