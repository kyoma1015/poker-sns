# Release backlog — 2026-10-20 integration update
通常開発はcodex/integration-poll-only-20261020で再開可能。本番リリースは未承認・BLOCKED。
- B/D/A/SNSはPR #11/#10/#9/#12由来を順次統合。詳細INTEGRATION_VERIFICATION_20261020.md。
- 質問箱は廃止・公開対象外。アンケートのみ。既存データ/内部DB/歴史資料は保持。
- 隔離DB未構成：通知の真正性/冪等性/旧INSERT権限、投票匿名性/履歴/通知/締切一回実行の検証が必要。
- production依存のaudit high 2（undici/@fastify/busboy）の互換修正・到達可能性調査が必要。
- Dの実認証保存/PNG/36分類QA、B公式問題照合は未完了。
- Cのvendor依存1,588ファイル、G11基準資料、complete checkpointは未確認。C_GTO.md参照。
- #4/#5は後継PRとの重複。旧ブランチ/元成果物を削除しない。
- mainマージ、SQL/権限変更、本番デプロイは明示承認が必要。今回は実施しない。
