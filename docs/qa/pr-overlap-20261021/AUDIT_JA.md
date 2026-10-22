# Open PR継承・差分監査（2026-10-21 UTC）

対象29件。各base/head/fullSHA、GitHub変更file/status/patchはopen-pr-snapshot.jsonへ固定。Git履歴祖先判定はpr-ancestry.json、全共有file/blob比較はpair-file-overlap.json。ファイル重複は機能重複と同一視しない。

## 正本候補・依存・二重取り込み回避

|PR|base → head|継承・扱い|
|---|---|---|
|#2|main → feature/poker-id-card|独立したPoker IDカード試作。後継統合未確認、維持。|
|#8|main → chore/autonomous-dev-foundation-20261020|開発基盤初版。継続workerの実装正本は26→34→36。|
|#9|main → codex/f03-selective-regression-20261020|F03通知RPC独立修正。13/21に同等取り込みがあるが本番DB検証別ゲート。|
|#10|main → codex/diagnosis-phase1-regression-20261020|診断第1段階。対象診断sourceblobは13と一致し、18→24→35へ継承。|
|#11|main → codex/tda-auth-network-guidance-20261020|TDA認証案内。TDA sourceblobは13と一致、14→23→32へ継承。|
|#12|main → codex/sns-poll-privacy-regression-20261020|poll-only旧候補。13の統合証拠、公開候補はmain基準の31。|
|#13|main → codex/integration-poll-only-20261020|旧B/D/A/SNS統合snapshot。個別新PRと重複一括merge禁止。|
|#14|codex/integration-poll-only-20261020 → codex/b-tda-quality-continuous-20261020|TDA transport/parser。23→32の実祖先。21のTDA sourceblobと一致。|
|#15|main → codex/a-http-security-release-20261020|HTTP依存security-only main基準。17の同依存変更、31の選択再利用と二重適用禁止。|
|#16|codex/integration-poll-only-20261020 → codex/continuous-queue-controls-20261020|有限queue基盤。26→34→36が後継。|
|#17|codex/integration-poll-only-20261020 → codex/a-security-ui-continuous-20261020|A HTTP依存＋共有UI。security-only15と重複、共有UI部分は独立維持。|
|#18|codex/integration-poll-only-20261020 → codex/d-diagnosis-quality-continuous-20261020|診断async隔離。24→35の実祖先。21の診断sourceblobと一致。|
|#19|main → codex/b-tda-rpc-isolated-release-20261020|B main基準のquiz RPC slice。14と同じ75編集行、認証guard文脈のみ異なる。新B固定入力へ通常merge済み（個別紛争解消記録）。|
|#20|codex/integration-poll-only-20261020 → codex/c-gto-active-milestones-20261020|GTO再構築/169/checkpoint。25→33の実祖先、21 checkpoint blobは完全一致。|
|#21|codex/integration-poll-only-20261020 → codex/continuous-combined-check-20261020|旧4系列横断検証snapshot。17/14/18/20/16を組み合わせた証拠用。独自の本番承認なし。|
|#23|codex/b-tda-quality-continuous-20261020 → codex/b-issue22-audit-20261020|B offline CLI安全性。32の実祖先。|
|#24|codex/d-diagnosis-quality-continuous-20261020 → codex/d-issue22-audit-20261020|D score行整合監査。35の実祖先。|
|#25|codex/c-gto-active-milestones-20261020 → codex/c-issue22-settlement-20261020|C settlement synthetic parity。33の実祖先。|
|#26|codex/continuous-queue-controls-20261020 → codex/issue22-real-workers-20261020|host worker/controller。34→36が後継。|
|#27|codex/issue22-worker-input-a → codex/issue22-host-a-fix|poll option数境界。31へ同修正を選択再利用済み、独立二重merge禁止。|
|#28|codex/issue22-worker-input-b → codex/issue22-host-b-fix|B空offline export判定。32と異なる関数修正で別途選択統合が必要。|
|#29|codex/issue22-worker-input-c → codex/issue22-host-c-fix|C reach mass overflow境界。33と別ファイル、別途選択統合が必要。|
|#30|codex/issue22-worker-input-d → codex/issue22-host-d-fix|D persona回答監査。35 UI修正とは別ファイル、別途選択統合が必要。|
|#31|main → codex/issue22-poll-only-release-20261020|アンケートmain基準公開候補。DB56PASSだが本番parity/Auth/SQL承認未完了。|
|#32|codex/issue22-b-answer-input-20261021 → codex/issue22-b-saved-answer-20261021|B保存回答の正当性・採点保護の現継承先。次検索raceは未実装。|
|#33|codex/c-rank7-input-20261021 → codex/c-rank7-20261021|C rank7 synthetic比較の現継承先。次budget検証は未実装。|
|#34|codex/issue22-recovery-input-20261021 → codex/issue22-continuation-recovery-20261021|復旧/候補抽出の基盤。36はその固定入力・起動診断資料。|
|#35|codex/issue22-d-doubleclick-input-v2 → codex/issue22-d-doubleclick-fix-v2|D doubleclick防止の現継承先。次error redactionは未実装。|
|#36|codex/issue22-continuation-recovery-20261021 → codex/issue22-independent-launch-20261021|固定次入力/起動診断。code実装完了や常駐稼働の証拠ではない。|

## 次B/C/Dの実証

- C：PR21 checkpoint sourceは候補入力と完全同一blob(dd26b7cab84b1e5de3dbabda41c04087e2746ce1)。PR20は真の祖先。新budget受入失敗は既存処理の未修正を示す。単なるパス重複による停止。
- D：PR21診断sourceは候補の祖先PR18と完全同一blob、PR10は祖先PR13と完全同一blob。PR21の全対象patchは候補へreverse-apply check成功。現35のdoubleclick差分を保持し、次のerror redaction受入は2FAIL。
- B：PR21 TDAは祖先PR14と完全同一blob、PR11は祖先PR13と完全同一blob。PR19だけは全file reverse/3way no-op証明が成立しない。そこで独立新入力branchで通常mergeし、全17変更fileと6競合を個別レビューした。旧19のquiz編集75行は祖先14の編集列と一致。現source、package/config、旧browser testsのsupersetを全てbyte維持し、独自QA資料は保持した。-s oursやignorelist不使用。

B再整理input：7ee09c1b3bf71a75e3889951d7520bf3347ba375 / codex/issue22-b-search-reconciled-input-20261021。元19が真の祖先となり、固定protected3hash不変、検索race baseline5FAILを再実測。実装未着手・lease未取得。解消記録は当該input docs/qa/pr-overlap-20261021/B-PR19-reviewed-integration.json。

## 制約

既存PR/branchのclose・rebase・merge操作なし。新しい独立入力branch内のレビュー済み通常mergeのみ。main・本番・DB・課金・過去checkpoint無変更。JSONのsame_head_file_countは共有fileのblob同一性であり、PR全体が不要という判定ではない。PR headが変化したらこの固定証拠を流用せず再監査する。
