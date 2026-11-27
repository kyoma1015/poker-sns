# 統合solver根本監査 — 正式品質FAIL、正式受入0/12

基点 cdeb899d68eb70dabb7291501d4db1674aa4836b、Draft PR120。
実行2026-11-26 UTC、再起動後の保全確認/確定2026-11-27 UTC。
**初回版は未完成。正式RFI0/3bet0。HU50を初回版へ縮小していない。**
2〜9人・正式20stack・全位置・RFI/3bet必須・可能な4bet・169混合頻度/EV・MTT/ring・ante/rake・不均等stack・正式12条件を維持。未承認値は採用しない。

## 原因として確認できたこと／未特定のこと

1. raw CF/regret/average/EVの符号、chance/card removal、own/opponent reach、root proposal除去、native pot精算は独立dense/path oracleと一致した。**単一の算術バグを原因とは特定していない。小規模oracleの一致は全native品質証明でもない。**
2. public-action samplingのraw推定が不偏でも、その都度のclipは完全列挙更新と同じにならない（E[max(0,R+g)]とmax(0,R+E[g])の差）。小規模nativeのroot勾配平均を維持しつつ、baselineで分散4.383648→2.236406、約49%低減。大きいimportance weightは残り、旧last次stepでもseed1最大inverse proposal1,727,555。
3. warm root保存行は86/169、81/169。残りは微小初期R/Aで、保存行と有効初期量が異なる。学習current regret方策と報告average方策も違う。`warm-mass-audit.json`。平均頻度を保つ同一擬似量へのrebaseは実装・照合したが、seed1単独対照では改善せず、単独解決策と認定しない。旧preflop全2631行はseed1の値で、seed2は2384行（前報の両seed同数表現を訂正）。
4. 多数の未更新opponent行を永続化していた。43更新の428879行中regret更新済み234390。lazy allocationで読取り専用の未学習行を一時mapへ移し、更新R/AとRNGを完全一致させたまま保存行25317→15117（約40%減）を実測。
5. 評価ゲームの相違が大きい。884ノードへのaction条件付けでは最大除外質量が約.97〜.99に達する。投影NCは完全native NCではない。粗いkey候補のBRまで粗くすると比較が不公平なので、新primary比較では全候補共通のexact own hole＋visible board情報でBRを計算した。未来boardはBR情報にも渡さない。
6. 自己対戦SB EV増加は品質改善ではない。新しい学習lastはseed1のEVが有意増加したが、両seedともBB river-jam逸脱の正の利得下界が見つかった。選択t0の棄却を単なるscoreノイズだけで説明できない。

推論：高分散のpublic-action sampling、情報集合/公開履歴の被覆不足、抽象化と省略サイズが主要課題。各寄与を全nativeで完全分離したとは主張しない。新しいNN/DCFR等を追加し続けず、失敗したfullgame学習の拡大を停止した。

## 実装・採否

既存`integrated_native.cc`/`integrated_solver.py`を拡張し、旧default動作を保持した。
- action baseline：全private vector/current opponent range/native passive rolloutを**control variateだけ**に使用。`b_a+1[A=a]*(v_child-b_a)/q_a`で補正する。passiveを継続方策として採用しない。sampled未来boardは学習用値計算だけに使い、policy key/queryへ渡さない。
- lazy rows：opponentの未学習lookupを一時領域へ移す。新active監査では有効。row capを無条件に引き上げていない。
- signed regret/uniform average、key-coarsening、behavioral warm rebaseは同じ更新器の対照用option。**新方策として正式採用したものは0件。** 粗いkeyではpriorも同じ情報で一定になるよう調整するため、keyだけの効果と混同しない。
- independent BR：private pair terminal積分を再利用し、同じ情報集合の全board/handを集約してからactionを最大化。独立既存dense kernelと照合。
- transfer lemma：一様continuation/chance誤差、追加サイズ/情報の逸脱上界が全部証明されない限り、native上界を返さない。詳細`RESEARCH.md`。
- checkpoint：同じraw bytesをzstd1で保存。実124094587byteでgzip9 CPU3.803秒/19328589byte、zstd1 CPU.543秒/19642687byte、展開SHA一致。学習CPUとI/Oを分離し、旧gzip出力も保護。

## 旧checkpointの縮約NC

旧best=t0、旧last=t43/t33を混同していない。固定2board/884ノード・旧抽象情報で再測定：
- seed1：18.154938→18.549840BB
- seed2：7.063374→9.492192BB

`history-*.json`。action投影あり。異なるboard law/情報集合の他研究NCと横比較しない。

## 同じゲームでの収束対照

既存CSR/private-vector CFRを再利用し、同一884ノード・2board law・初期方策・情報集合で、全chance積分とpublic-chance samplingを比較。**両方ともpublic actionは列挙する。** それぞれ純学習CPU90秒、4/16/64/256段階。新しいfullnative outcome samplerとの完全な同ゲーム比較とは区別する。

| seed | 全chance積分：初期→最終NC | 更新数 | chance sample最終NC | 更新数 | 全chance方策に情報を細かくしたBRのNC |
|---|---|---:|---:|---:|---:|
|17120101|10.400928→0.124835|244|0.191199|280|1.057948|
|17120102|3.427254→0.117465|260|0.165834|338|1.058656|

約659〜713MB RSS。独立BR計算との一致と次step再現を確認。coarse native方策を既存kernelへ写す際の同一情報集合内の頻度差は0（`mapping-audit.json`）。同一ゲームではCFRが収束する一方、情報抽象化を外すと約1BB残る。これは**固定有限game内の追加情報による攻略可能性**で、実native誤差上界ではない。

初回の2block constructorは継承したdense用メモリ見積りで拒否された。既存one-block初期化＋streaming blocks interfaceを使い、kernelの512MiB制限は変更していない。実RSSは上記の範囲。拒否したrunを学習成功に数えない。

## Fullnativeの対照・独立最終評価

fullnative対照は同じCPP、RNG、CPU-budget条件でfine/coarse、clip、baseline、warm-rebase/signed-uniformを比較。全primary best選択はt0。途中のabstract-BR pilotも別保存し、正式PASSにしない。実際に学習した事前指定のsigned/coarse/baseline lastを**診断用候補**として独立評価した。選択t0を学習成果に改称していない。

旧Sparse、旧PCS、旧統合best、新学習lastの4方策を同じ16384world/seed17138701で対応付け比較。最終データで候補を選び直していない。family99.9%を両seed200eventsへ配分。

| 指標BB | seed1 新last=t127 | seed2 新last=t16 |
|---|---|---|
| SB EV |1.244643 [0.433010,2.056277]|-.098373 [-.747291,.550545]|
| 旧SparseとのEV差 |+1.156684 [.132032,2.181335]|-.331729 [-1.233970,.570512]|
| 3.5BB逸脱 |.053742 [-.968031,1.075514]|-.237393 [-1.085712,.610927]|
| 8BB逸脱 |-1.437281 [-2.551014,-.323549]|-2.043195 [-3.026065,-1.060325]|
| 10.5BB逸脱 |-.279443 [-.873733,.314847]|-.077265 [-.576449,.421918]|
| river jam逸脱 |2.223816 [1.380606,3.067026]|1.586517 [.807779,2.365255]|

7BB、river nuts、SB foldも評価。負の逸脱点推定は安全証明ではない。**完全native BR/NashConv上界はUNKNOWN**。river jamからの利得下界が両seedで正なので、この候補は不合格。

新lastのriver regret/average独立再利用は425/6969=6.0999%・315/6969=4.5215%、68/7091=.95896%・49/7091=.69102%。turnは868/7280=11.923%・627/7280=8.613%、150/7854=1.910%・115/7854=1.464%。旧lastの別dataset .173/.087%、0/0%を直接同条件の改善率とはせず、新しい比較条件/件数を明記する。旧PCS85.78/87.76%を新候補の成果としない。coverageだけでは採用しない。

純学習CPU30.101秒/127更新、1.925秒/16更新（seed2早期悪化停止）。peak RSS662/512MB。root support12/99、87raise省略。任意native合法サイズへの応答能力を全サイズの品質保証としない。

## EV精度・多人数

旧root33462測定、Fold1014厳密、Jam493提案精度を変更していない。新digestではroot/vs-open/vs3betの各169頻度を保存、Fold1014厳密、Jam196（49/147）が提案halfwidth<=.05BBに到達。正式精度合格0。異なるdigestの493と196を合算して品質達成としない。新候補は精度到達数自体も増えていない。A7の承認・全action・BR/誤差証明が別途必要。

旧3人exact .023738946BBとK4 oracleを保護。6/9max各2seedの既存checkpointから、iidとprivate deal-slot rotationを同じCPU6秒budgetで継続。全1024world/allseat対応付きEVで有意改善なし。rotationはchance lawのbijectionであり、stack/seat/方策を回転させない。一般的多人Nash収束は保証しない。8新checkpoint次step一致。

N試験の`CPU_seconds`フィールドはtraining＋serialization＋nextstep replayを含む。純学習時間として報告しない。`multiplayer/timing-clarification.json`と実行source保存。将来driverはclockを分離するよう修正し、同じ試験を無意味に再実行していない。

## 資源・正式初回版への限界

環境表示はlogical CPU3、host RAM約9968MiB。再起動後の実cgroup上限はCPU2core・RAM8GiB（manifest）。旧run時点のquotaは未記録なので表示値を割当量と混同しない。開始時disk空き約5.9GiB。CPU/容量の追加購入なし。QA予算512MiB内（確定サイズはmanifest）。95時間学習は行わず、各native試験30CPU秒以下、同ゲームoracle90CPU秒、明確な早期停止とcheckpointを使用。checkpoint圧縮/復元負荷は学習CPUへ足していない。

現在のroot/path/table表現を全20stack・全人数・不均等vectorへ総当たりすると実用化できるという証拠はない。承認案の等stackだけで2560game/14080position profiles、最低1946880RFI行。全域の資格計算時間・保存量・cache miss時間はUNKNOWN。Python lookupをアプリ全体応答時間としない。

事前計算＋証明書付きcache＋局所計算の構成を維持する。現実的な次工程は、収束を確認した全private/public action積分を、active sparse index/適応supportの有界subgameへ接続すること。ただしsafe continuationのuniform CF/error envelope、全合法サイズの逸脱上界が必須。現在はその証明を実装し切れていない。保守的な一様sampling証明の例ではn約2e11となり、無料環境でこのrouteは現実的でない。全手法の不可能性や完成予定日は断定しない。

`acceptance.json`に正式12条件の不足・依存・必要実装・計算量UNKNOWNを記録。全12false、正式RFI0/3bet0。正式20stack、MTT/ICM、ring rake/cap、ante、サイズ、不均等stack、A7値は既存承認案を維持。承認だけで今回の品質不合格は解除されない。

## 検証・再開

ローカル全167回帰PASS200.249秒、新4回帰PASS114.135秒（同時に有界試験を実行）。正確なコマンドは`verification.txt`。production/UI変更なしでnpm/browser対象外。CI成功はGTO品質の証明ではない。

- 旧source/defaultのlast=t43/t33は旧binaryと新binaryで次step raw bytes一致（t44/t34）。`legacy-nextstep.json`。
- 新診断last：`ablations/{17120101,17120102}/coarse-signed-rebased-uniform-baseline-physical/last/`。bestはどちらもt0。`integrated_audit_native.restore`が実行driverの保存sourceも照合。
- 同ゲームcontrol：`same-game/{17120101,17120102}/{exact,sample}/checkpoint.npz`＋`rng.json`＋`identity.json`。
- 新last2件/control4件ともsource/build/SHA/RNG照合後の次step再現を実測。`final-checkpoint-replay.json`、再現driver同梱。自動再開は実装していない。
- 棄却pilotのsource snapshotsとCPを保持。古いsource/buildの全pilotが現wrapperで無条件復元できるとは主張しない。identityを黙って置換しない。
- 一部仮driverの初期化エラー/未freeze digestは修正後に実証した。失敗をPASSに数えていない。Git以外の旧研究DB/ZIP/未push bytesは利用できず復旧済みとしない。

本番DB/Storage/SQL、本番Vercel、main merge、SSO解除、課金、force-push、成果削除、未検証registry登録なし。通常commit/push後の新CIのみ確認する。
