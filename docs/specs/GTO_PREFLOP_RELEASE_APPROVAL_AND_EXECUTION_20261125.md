# 初回版・一括承認パッケージと実装経路 v2

作成: 2026-11-25 UTC。状態: **PENDING_USER_APPROVAL / DESIGN_NOT_EXECUTED**。
基準コード: 402ae5efe1bdf5c10ffe4b7ae76a183c088c7066、Draft PR120。
旧資料の原典復元・承認済み扱いではない。既存正式受入12条件を削除・緩和しない。
HU50は検証地点。正式初回版の2〜9人、20stack、全位置、RFI/3bet、
vs3bet/可能な4bet、169混合頻度/EV、ante/rake、不均等stackを維持する。
承認は仕様だけを対象とし、品質PASS・通常registry登録・公開・merge・本番操作・課金を承認しない。
既存の承認済み要件に本案より厳しい条件があれば既存条件を優先する。

## 1. 一括回答用の決定表

「A1〜A7を承認。A4はM1/M2/保留」と回答できる。
保留は要件削除ではなくBLOCKEDのまま。条件を承認しても未検証戦略は未検証のまま。
不明な原典・ICMの要否を暗黙に決定しない。

| ID | 推奨・具体値 | 選択肢・理由 |
|---|---|---|
| A1 正式20stack | **2,3,4,5,6,7,8,9,10,12,15,20,25,30,40,50,75,100,150,200 BB**。ante/blind支払前の各席開始stack。SB=.5BB、BB=1BB | 既存案Aを維持。short2〜10、既存MTT候補、HU50、cash100、deep150/200を含む。代替は旧資料の中深度20値案。採否未定 |
| A2 人数/位置 | **2,3,4,5,6,7,8,9人、全席**。seat0=SB、seat1=BB。HU BTN=SB、それ以外BTN=N−1 | 人数/位置は削減しない。表示名は下表。欠損位置を別位置の戦略で埋めない |
| A3 サイズ | **1BB=2chip、.5BB刻みの全native合法raise-to**、fold/check/call、short all-inとreopen権を含む。RFI表示例2/2.5/3/3.5BB、3bet表示例8/8.5/9/10/10.5BB、4bet表示例20/21/22BBとjam | 代表値は入力例で評価範囲ではない。最小raiseやstackで違法な例は表示しない。全raise回数/後続履歴を保持。代替.25BB格子は新しいchip/config identityが必要。連続実数全sizeを解いたとは主張しない |
| A4 モード | **M1:MTT chipEV+rake0、ring7条件**。MTT BBante0/1BB。ringもBBante0/1BBを明示profile化 | M2:MTTにICMも含む。ICMはpayout/全残存stackとEV単位・誤差閾値が別途必須。原典でICMが必須ならM1だけで#6をPASSにしない。要否未確認なら保留。既存要件からICMを除外しない |
| A5 ante/rake | BBante **0または1BB**、ante-first、stackは支払前。ring: **0%、5% capなし/5BB/10BB、10% capなし/5BB/10BB**。no-flop-no-drop、whole-hand cap、chip単位floor、anteをrake対象、terminal徴収、dead eligibility=all_live | 既存案のhouse-rule値を一括選択可能にしたもの。方式・丸め・capの違うgameを同じdigestにしない。個別ante等が既存要件なら別profileを追加し、BBanteへ置換しない |
| A6 不均等stack | 全席の実stack vectorを入力。**各.5〜200BB、.5BB刻み、支払前、正値**。各席stackを単一effective stackに丸めない | 最小検証族:各S∈A1の等stack、1席short=S/2、1席deep=min(2S,200)、S×(1,.8,.6)循環を全席rotate。試験値は.5BB格子へ事前定義して重複除去。利用者入力を勝手に丸めない。**これは検証の最低族で全域の品質証明の代用ではない**。入力受理≠品質合格、未資格vectorはNOT_QUALIFIED。既定要件がさらに広い場合は原典範囲を優先 |
| A7 品質具体値 | 各playerの完全target game一方逸脱gain上界 **≤.05BB/hand**。HUでさらにNashConv上界 **≤.1BB/hand**。全169/表示actionの**条件付きEV half-width≤.05BB、familywise confidence≥99.9%** | 旧C案の数値であり未承認。より厳しい代替.02BB。ICMの金銭/賞金EVへBB値を流用しない。完全BR不明はUNKNOWN。不採用sizeを0誤差扱いしない |

### 位置名

| N | seat0,seat1,seat2以降 |
|---|---|
| 2 | SB/BTN, BB |
| 3 | SB, BB, BTN |
| 4 | SB, BB, CO, BTN |
| 5 | SB, BB, HJ, CO, BTN |
| 6 | SB, BB, UTG, HJ, CO, BTN |
| 7 | SB, BB, UTG, LJ, HJ, CO, BTN |
| 8 | SB, BB, UTG, UTG+1, LJ, HJ, CO, BTN |
| 9 | SB, BB, UTG, UTG+1, UTG+2, LJ, HJ, CO, BTN |

別名はUI aliasとして扱い、seat/public履歴で識別する。BBの「全員fold後RFI」は
native終局であり、架空の判断行を生成しない。他位置/BBのvs-open等は省略しない。
A4-M1はICMの要否が未解決のときに全MTT受入を完了させる選択肢ではない。

### A7に必要な証拠

- 同一config/source/build/RNG、同一方策digestを固定し、生成・選択・独立最終評価を分離。
- confidence family（全profile/全169/全action/全主張）の範囲とδ配分を事前固定。
  profile別99.9%をrelease全体99.9%へ無条件に合算しない。
- native合法性、正確なカード除去、Bayes range、chance reach、全席情報制約、
  side pot/uncalled返金/ante/rake/不均等stackを独立oracleで照合。
- EVは固定方策の条件付きEVとroot寄与、GTO最適EVとの差を分ける。
- 縮約BRだけを完全native BRと呼ばない。独立BR上界の意味・対象集合を明記。
- 抽象化/継続payoffの一様誤差εと省略action gain上界ωを個別に検証。
  旧C案: **model gain + 2ε + ω ≤ .05BB**、目安ε≤.01BB、ω≤.01BB。
  最終的なgain上界を満たさない内訳予算はPASSにしない。
- N≥3は一般的Nash収束定理を前提にせず、各playerの独立一方逸脱を検証。
- 数値的不変条件の提案:保存確率は有限/非負/総和誤差≤1e−12、
  違法action確率0、全169行と全必須profileを検査、native chip cashflowは厳密保存。
  これらのソフトウェア検査PASSだけでGTO品質PASSにしない。
- 12条件の各条件に全対象profile coverageと証拠を紐付け、合格certificateと検索結果の
  digest一致まで確認。UNKNOWN・未訪問prior・未測定EVを正式行へ昇格しない。

## 2. 必要量と技術的限界

上のM1/ante案を全部採る場合の**等stack部分だけ**の下限:
20stack×8人数×(MTT1+ring7)×2ante=**2,560 game profiles**。
全seat数合計44より14,080 position profiles、BBの架空RFIを除く36位置より
最低**1,946,880 RFI頻度行**。vs-open/vs3bet、size/履歴、不均等stackは別に増える。
これは提案から算出した数量で、承認済みcoverageや必要学習時間ではない。

HU50 root169×99×2方策=33,462セルは測定済みだが、精度合格0。
仮に[-50,50]BBの各cellにhalf-width.05BB、33,462cell全体δ=.001を
素朴な独立Hoeffdingで求めると、最悪上界は約**36,038,137標本/cell**、
全体約1.21兆rolloutになる。これは保守的な**計画上の例**で、実必要標本数や
所要時間の実測ではない。現在のworld数だけを増やす経路は採らない。
条件付き積分・層化・共通乱数・private-vector計算で下げられる量はpilotで測る。
完全native BR上界/一様抽象化誤差の証明計算量は現時点UNKNOWN、完了ETAは提示不能。

## 3. 根本設計の選定（未実装・未測定）

### 確認済みと仮説を分離

確認済み:両seedのriver regret+average再利用0、turn平均再利用1%未満、
詳細controlと新候補の自己対戦EV列が同一、33462cellの条件付き区間は最大100BB。
3人Sparse64更新のgain2.172906/2.930922は既存exact32の.023738946に届かない。

ソース確認:fullstreet_core.ccのfs_worldは公開5boardに適合する1081私有handと
カード非重複pair法則を既に構築し、fs_evalはcurrent policyのreachを再計算する。
ただし既存fs_evalには**action数≤4**の固定layout制限があり、新12supportへ
そのまま接続できない。凍結kernelを変更せずadapter/新CSR layoutで拡張する。

仮説（未実測）:1worldの私有dealだけを学ぶSparse方式は、正しいchance法則でも
条件付きgradient分散・情報集合被覆が不足する。CFR+のclipは
E[max(0,R+g_hat)]とmax(0,R+E[g_hat])が異なるため、期待値oracle一致だけでは
小予算の収束品質を保証しない。これを3人exact対照で因果分解する。

別の整合性検査:共有keyで省略したprivate/board情報をwarm priorが参照していないか。
sparse_native.ccの共有keyと、warm lookupの169hand/fs_feature/fs_nutsは情報粒度が
異なるため、同じkeyの初期確率が物理worldで変わるかを検査する。**バイアスが
実測されたとはまだ主張しない**。同時更新・合法性・カード除去の旧修正は保持する。

### 比較して最初に実装する候補

| 方式 | 判断と再利用 | 実装前の失敗条件 |
|---|---|---|
| flat key圧縮だけ | 前回有意改善なし。拡大学習しない | 再訪率だけ増えBR/EVが改善しない |
| **public chance sampling＋private vector積分（第一候補）** | fs_world/fs_eval/CF-vectorの資産を再利用。public boardを層化し、適合する私有handを積分。rank-prefixとcard blocker補正のcacheでpair計算を共有 | chance補正/情報制約/gradient期待値がoracle不一致、同budgetの独立品質が悪化 |
| 階層的情報集合抽象化 | private169の記憶、過去feature prefix、公の履歴を保持。made rank/draw/blocker/potentialを併用。階層の残差を別に測る | 単純equity bucket、private記憶忘却、初期priorが共有keyに非整合 |
| range-conditioned continuation value | 同じjointゲームのcurrent reachからCF-vectorを計算。旧rangeで固定したpayoffを新rangeに流用しない | range凍結、相手の実hole/未来boardの方策入力、恒常的payoff bias |
| 局所subgame solving | 必要なときだけactual publicstate/条件付きrangeで再解く。範囲を小さくし、safe gadget等の仮定と誤差を明示 | blueprint CF値や安全性条件が不明なのに「safe」と称する |
| 適応size/off-tree応答 | actual native履歴を保持し、独立逸脱のLCB/UCBで追加対象を選ぶ。新sizeと後続応答を一緒に学習 | 未評価sizeを0誤差、単純fold補完、既知1sizeだけのpatch |

PCSの実装は**同じjoint CFR+の計算形態変更**で、新しい研究solver群を乱立させない。
public boardを先にsampleし、残り47枚からのprivate pair法則を厳密に作ることで、
元のuniform52 joint chanceと一致させる。flop strataのproposalがtargetと違うときは
既知のp(stratum)/q(stratum)で補正し、private blockersを無視しない。
方策が見るのはown hole・そのstreetまでのboard・公開履歴・推定rangeだけ。
terminal評価用の完成board/全holeはpolicyへ渡さない。

private pair密行列の反復再計算を避ける実装候補:
相手rangeのrank別prefix sumsと、hero各cardを含むhandの補正を使う。
互換性massはtotal−cardA−cardB+samehand。win/tieのrank条件も同じ包含排除で照合する。
この高速化は**未ベンチマーク**。HUだけの2player演算をそのままN人へ流用しない。

### 最初の実行ゲート（実行環境復旧後）

1. 小規模有限ゲームでPCS/全列挙のunclipped gradientとaverage期待値、
   card除去/chance/Potを照合（許容目安1e−10、正式GTO閾値ではない）。
   同じ抽象化gameの完全列挙BRと、native情報を持つBRを分けて測る。
2. 3人4world exact対照に対し、(a)chanceだけ全積分、
   (b)opponent actionだけ全積分、(c)両方、を同budgetで比較。
   E[raw gradient]とclip後・平均方策の差を分離。旧exact .023738946を保護。
3. 初回HU pilotは**各候補/seed10秒、512MiB、保存100MiB**上限、
   2seed、training/selection/final seed分離。N pilotは既存3秒目安の完了batch境界を
   基準にし、計算/保存/評価時間を別記する。見込みなしなら拡大しない。
4. 再利用率はaverage-only、regret-only、両方を分け、>1合法actionの判断だけを数える。
   両seedのriver「両方」>0は必要な工程gateであり品質PASSではない。
5. frozen旧方策と新候補を共通worldで比較し、**対応付き改善の独立区間**を保存。
   3.5/8/8.5/10.5BB、その他native合法size、river jam/nutsを含める。
   学習量だけを増やさず、EV区間・独立BR・抽象化誤差を併記する。
6. dense EVはRFIだけでなくvs-open/vs3betへ拡張。rare-handの逆重みを使うより、
   ownclass層化・opponent conditional積分・既存all-in cacheを再利用。
7. public treeはCSR可変actionとnative ledgerで整合。サイズ追加後にrange/後続CFを更新。
   fullnative BR上界がUNKNOWNならcertificate/registryへの正式登録はしない。
8. 再開にはR/A、RNG、range/chance law、support、親リンク/timeline、config/source/build
   hashと停止理由を保存。自動再開サービスがあるとは扱わない。

## 4. 12条件の最短経路・依存関係

全条件の正式PASSは現在0。下表の「最短」は優先順であり達成予測ではない。

| # | 不足・最短の具体的実装 | 依存/必要計算・限界 |
|---|---|---|
| 1 RFI | PCS/private-vectorでHU50の有効なpostflop決定を学習、独立BR品質gate | 環境、同game oracle、A1〜A7。最終BR計算量UNKNOWN |
| 2 vs-open/3bet | 同じjointゲームで全合法openへ応答を共同学習 | #1、可変support/CSR。12/99だけで完了しない |
| 3 vs3bet/4bet | 全169 conditional actionEVと合法再応答、4bet/shortjamを検証 | #2/#5/#11。非法履歴はnative証明でN/A、条件自体は削除しない |
| 4 169頻度 | 全必須profile/位置を生成、prior行を分離、確率不変条件 | #1〜3/#6〜11。等stackRFIだけで最低1,946,880行（本案） |
| 5 EV | 条件付き期待値/層化/blocked range prefix計算、vs-open/vs3bet測定 | 33462測定済み≠精度合格。素朴MC最悪量は上記、実必要量UNKNOWN |
| 6 MTT/ring | A4/A5のprofile/config identity、モード別EVと品質証拠 | ICMが必要なら単位・全残存stack/prize入力の別gate必須 |
| 7 2〜9人 | exact3→variance低減N→6/9→残る4/5/7/8を同じ実装で検証 | N CF/reach、lazy average。一般Nash保証なし、一方BRが必要 |
| 8 20stack | A1一覧/支払基準を承認後config化、coverageを生成 | 0/20正式値採用。未承認は研究用のまま |
| 9 全位置 | 上のseat表、全位置のRFI/vs-open/vs3bet/行動履歴 | #4/#7/#8、44位置/等stackモード組。別位置で補完しない |
| 10 ante/rake/不均等 | native cashflow/sidepot/返金を保持しA5/A6のstrategy品質を検証 | 精算の回帰PASSだけでは品質PASSにならない。入力全域の証明未達 |
| 11 サイズ | generic support追加、actual off-tree応答、omitted gain上界 | 各native合法size、後続public history。物理100BB上限は禁止 |
| 12 検索 | 合格済み同digest certificate→registry→実検索の対応を検証 | #1〜11と既存受入規則。未検証を通常GTOへ出さない |

## 5. 環境復旧の具体的条件と今回の限界

管理APIは対象instanceをrunning/connectedと返すが、実行APIは
「No usable execution environment is available」を返した。状態変化後の1回再確認も同じ。
前回のnative_git障害が現時点でも同じ原因で継続しているとは断定しない。
**実行チャネルの接続/選択不整合が現時点のBLOCKER**。同一失敗を無限に再試行しない。

復旧条件:
- この会話で選択された正常なCloud環境に実行ツールが接続し、pwd/gitが応答する。
- /workspace/poker-sns（または明示された新checkout）で現在remote HEADをread-only確認。
- 未保存差分/未push commitがあれば先に保全し、削除/reset/cleanしない。
- 402ae5eのsourceとcheckpoint manifest/rawSHAを照合。旧binary identityが再現できない
  場合は旧成果を残し、新build digestで再検証してから学習へ使う。
- HU: docs/qa/sparse-generalization-20261124/hu-final/{17120101,17120102}/compact/best/
- N: docs/qa/sparse-generalization-20261124/multiplayer-lazy/
  R/A/RNGに加えlazy_info/behavior_historyを保持。sampling averageへ勝手に変換しない。

今回ここでsource/build/実checkpointの新環境復元やsolver実装・pilotは実行できていない。
読めたハッシュ台帳をbinary復元完了とは報告しない。提案・必要量は計画で、実測を捏造しない。
GitHub接続は利用できるため、本承認表・設計・依存経路を専用branchへ通常のfast-forwardで保存する。
既存402ae5eのCI8系列9SUCCESSはread-only確認済み。SUCCESS再実行・CIを通すためだけの
workflow変更を行わない。docs-only新HEADでworkflowが起動しなければその事実を報告する。

参考:既存APPROVALS.md、GTO_PREFLOP_RELEASE_PROPOSAL_20261117.md、
sparse-generalization-20261124/acceptance.json。いずれも本書で既存承認や品質PASSへ昇格しない。
