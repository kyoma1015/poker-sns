# GTOプリフロップ正式仕様案 v1 — 承認待ち

これは原典の復元結果ではなく、未確定事項に対する新しい提案です。
採用状態PENDING。既存ACCEPTANCE.mdの12条件を削除・緩和しません。
承認前の数値を正式registry・通常GTOへ登録しません。
原典調査は既存preflop-release-20261116/spec-provenance.jsonを再利用します。
O06の候補MTT10/15/20/25/30/40BB、cash100BBは下記推奨案に全て含まれますが、
正式20構成・全サイズ原典が復元できたという意味ではありません。

## 決定A：20スタックと条件の意味

推奨：2,3,4,5,6,7,8,9,10,12,15,20,25,30,40,50,75,100,150,200 BB。
20個の共通等スタックprofileをMTT chipEVとring、各2〜9人で対象とします。
全座席が同じ開始stack。stackはante・blind支払前、SB0.5/BB1。
BB anteは0/1BB、ante-first。通常の不均等stack・ICMはこの20等stackと混同せず、
要件から除外せず別の明示profileが必要かを決定してください。現受入条件は維持。

理由：短いMTTで変化の大きい2〜10BBを細かくし、既存O06候補、HU50検証、
標準cash100・deep150/200を含む。既存half-BB整数chip実装を再利用できます。
代替：5,7.5,10,12.5,15,17.5,20,22.5,25,27.5,30,35,40,50,60,75,100,125,150,200。
中深度を細かくする一方、2〜4BBを外すため、原典が短stackを含む場合は不適合。
原典回収を待つ案も可能ですが、未確定数値以外の実装・検証は継続します。
影響：設定registry、scenario生成、人数/位置別data coverage、stack/ante解釈のUI。

ring7profile推奨：0% capなし、5% capなし/5BB/10BB、10% capなし/5BB/10BB。
これは既存native対応条件の明文化案。MTTはrake0/ICMなしchipEV。
no-flop-no-drop、whole-hand cap、chip単位floor、anteもrake対象、terminal徴収。
これらのhouse-rule選択も原典確定ではなく、承認対象です。

## 決定B：全ベットサイズ

推奨：1BB=2chip、最小chip0.5BB。各実際のpublic historyでnative/referenceが
許す全raise-to整数chip（最小full raise〜all-in、および合法なshort all-in）を対象。
fold/call/checkも保持。preflopのraise回数による枝刈りは禁止。
RFI入力の代表open2/2.5/3BB、対openの3bet参考値等は検索の便宜に過ぎず、
他の合法サイズを精度評価の逸脱集合から消してはいけません。

代替B2：0.25BB刻み（1BB=4chip）。2.25BB open等を表現でき、action数は約2倍。
代替B3：疎な代表sizeで学習する。ただし承認された全legal sizeに対する
omitted-action gainの独立上界が必要。未評価sizeを0誤差として扱うのは禁止。

理由：推奨は既存native・Python参照実装をそのまま検証に再利用でき、
「全サイズ」の範囲が再現可能。連続実数全sizeを解いたとは主張しません。
影響：HU50 RFIですでに99合法actions、200BBでは399程度。現行64-action
transport上限・全action縦列表示は不足。承認後は数値を切り捨てず容量と表示を拡張。
0.25BB案ではchip解像度、snapshot/config/policy identityも変更し旧成果と分離。

## 決定C：最小正式対象と品質基準

最初のqualification対象推奨：HU50、MTT chipEV、ante/rake0、SB RFIと
SB2.5BB openに対するBB応答。全52枚・全street・全legal sizeを含む評価。
既存learned_small/largeの8候補を再利用するための最小の同条件です。
次の実用拡張は原典O06の6MAX cash100BB・rake0、各位置RFI/vsopen。
この小集合を満たしても、全12条件や2〜9人/20stack全体の完了とは数えません。

品質の推奨値（原典にない新しい承認対象）：
- complete target gameの各player一方偏差gain上界<=0.05BB/hand。
- HU zero-sumでは追加でNashConv上界<=0.1BB/hand。
- 全169classおよび表示する全actionのEV区間half-width<=0.05BB、
  familywise confidence>=99.9%。exact/rigorous numerical証明ならconfidence1。
- 固定model内のBRだけでは不可。profileと全逸脱を覆うmodel誤差を分離。
  model gain + 2*uniform payoff error + omitted-action gain <=0.05BBが必要。
  内訳予算の目安：uniform payoff error<=0.01、omitted-action gain<=0.01。
- 条件付きvsopen EVとroot gainを区別し、履歴reachとprivate-card除去を含める。

代替：各gain0.02BB、EV half-width0.02BBに厳しくする。検証量は概ね
誤差二乗の逆数で増加。0.1BBを「従来の正式基準」として流用しません。
実行時間・実現可能性は未確定。判定不能はPASSではなくUNKNOWN/BLOCKED。

## 現在の承認範囲

A/B/CいずれもPENDING。提案値に基づく評価はEVALUATION_ONLYと表示します。
通常GTOに登録できるのは、条件承認と独立品質証拠の両方を満たしたものだけ。
Draft解除・main merge・本番操作・課金・SSO変更の承認は求めていません。
