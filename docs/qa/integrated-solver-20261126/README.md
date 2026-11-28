# 統合solver / 2026-11-26 — 品質採用FAIL、正式受入0/12

基点1e91f2c1a8b34a4d03cd1e30420e9856076fb8ea、Draft PR120。
HU50は途中検証。正式2〜9人・20stack・全位置・RFI/3bet・可能な4bet・169混合頻度/EV・MTT/ring・ante/rake・不均等stackの目標を維持する。
**正式RFI0/3bet0、通常registry変更なし。統合学習後の方策は品質gate不合格で採用しない。**

## 実コード

`integrated_native.cc` は既存Sparseのnative action selectorとPCS private-vectorを同じゲームで接続する。全1081hand/1070190合法private pair、rank-prefix/カード除去を再利用。rootは全support actionを共通乱数で積分し、後続public actionは正のproposalでsamplingする。両ownerは固定preupdate方策を使い、生のCF regretを積分してからCFR+clipする。可変長action索引で4action制約を除き、任意のnative合法raise-toをpublic history単位に追加でき、その後続も共同学習する。未知履歴は既存合法warm priorを明記して用いる。単純fold補完ではないが、priorの品質は未検証。

自分の169class、全過去streetの戦略特徴、公開履歴をキーに保持し、対戦相手のhole/未来boardを方策へ渡さない。terminal積分だけが合法private pairを使う。suit同型・perfect-recall prefixを保持する代償として過細分化が残り、共有率/品質とも突破していない。全サイズ対応の入力能力と全サイズの学習/誤差保証を混同しない。

`integrated_solver.py` は元checkpoint全2631 preflop行/477 public履歴の全support/R/Aを取り込み、全行の平均頻度を1e-14で照合する。実checkpoint監査では再生成supportから欠落した旧actionは0件だった（`inheritance-audit.json`）。旧rootは実データで**11/99**、従来報告の12は訂正する。個別サイズ欠落を実不具合と主張しない。将来のsupport落ちを防ぐsynthetic14のcodec回帰も追加した。汎用discoveryは全省略rootサイズを32worldで順位付けしaction16を追加、最終12/99、87raise省略。discoveryの点推定は安全性証明ではない。

`integrated_precision.py` は同一digestのBayes prehistory rangeを全1225相手handで積分し、Foldを厳密計算、Jam後の相手fold/callを積分する。board標本は事前にposterior×callで層化割当、重み付きHoeffding区間。条件付きdecision EVとroot寄与/到達率を別保存し、root重みで区間を狭くして精度PASSにしない。すべての他actionのEVはUNKNOWN。

多人は既存external samplingを保持し、K chance worldの生regretを平均してclipする。N人reach・lazy average・カード除去を変更せず、K1の既存方式完全一致とK4の3人有限oracle期待値一致を確認。一般の多人Nash収束保証はしない。

## 評価・停止結果

正規最終結果は **support-preserved/**。`summary.json` に両seedのdigest、全逸脱区間、対応付きEV差を保存。

| seed | 純学習秒 | 更新数 / 選択数 | 学習peakRSS | native SB EV [区間] BB | 3.5BB逸脱利得 [区間] BB |
|---|---:|---:|---:|---|---|
|17120101|10.120|43 / 0|485,224,448 B|0.007702 [-0.488604,0.504007]|0.411763 [-0.259236,1.082762]|
|17120102|10.089|33 / 0|338,251,776 B|0.215097 [-0.336465,0.766659]|0.186896 [-0.535936,0.909728]|

選択seed17137401/512world、discovery17137301/32world、最終17137501/16384worldを分離。最終評価から候補を選び直していない。両seedとも選択gateでt0が残ったため、旧頻度を新学習成果とは扱わない。paired EV差は0 / +0.000244BBで有意改善なし。区間は2seed/100eventへの配分付きfamily99.9%。主評価と別studyを全部まとめた同時保証ではない。

学習後last checkpointの独立2048world(seed17137601、候補選択不使用)で、turn regret/average再利用は22/1200=1.833%・18/1200=1.500%、6/959=.626%・5/959=.521%。riverは2/1153=.173%・1/1153=.087%、0/795=0%・0/795=0%。選択t0の新学習行再利用は両seedとも0。旧PCSの85.78%/87.76%を新統合方式の成果として転記しない。

独立32768world(seed17136901)でPCS−旧Sparseの3.5BB逸脱悪化は+1.535355 [0.453785,2.616926] / +1.710111 [0.664979,2.755243] BB。過去のPCS悪化を両seedで確認し、その方策を採用しない。

旧v2/root prototypeも保存。seed2は独立選択で改善傾向を確認したため10秒で棄却せず、30秒/1.5GiBに段階拡大。t26→102→170、29.588秒、RSS1,221,664,768B、row上限停止。選択score .157→.382→1.471へ悪化しt26を保持、90秒拡大なし。収束不可能と断定はしない。原資料は`extension/`、`root-integrated/`、`source-v2/`、`source-v3/`に保存し、正規最終候補と区別する。

## EV精度

両seedで3context×169の頻度を保存。root/vs-open3.5/vs3bet10.5のFoldは各507セル厳密、Jamは277 / 216セルを提案halfwidth<=.05BBで測定。合計Fold1014+Jam493=1507セル。seed別Jam内訳100/98/79と113/94/9。各context約30秒、全世界から事前に割当したboard条件付き期待値を積分。CPU競合/時間予算で測定数が異なる。固定標本の完了セルだけ計上し、未完了セルを合格扱いしない。

**正式精度合格0セル**。±.05は承認案の数値試験にすぎず、正式仕様採用や戦略受入ではない。従来root33462測定セルを保護し、新digestの測定と合算して全域達成としない。全native BR/NashConv上界、継続/抽象化/省略サイズ誤差上界はUNKNOWN。物理的100BBをBR収束証拠にしていない。

prototype precisionの初回は実行中source編集があり、receipt-time SHAと実行sourceが異なった。`precision-prototype-provenance.json`と実行snapshotで明示し、その99セルを正規証拠に数えない。最終両seedはsource凍結後に実行、両receipt SHAは現在の`integrated_precision.py`と一致。

## 多人数・実現可能性

既存3人exact逸脱合計0.023738946BBを保護。新しいK4期待値oracleは独立path BR/regret/average、native pot精算と一致するが、新しい6/9maxの品質証明ではない。`multiplayer/results.json`に6/9max各2seed・K1/K2、同時間約3秒の継続学習と512world全seat評価/合法minraise逸脱を保存。K2の全seat paired EV区間は0を含み、有意改善なし。8研究checkpointの実nextstep再現済み。sidepot/refund/不均等stack/BBante/rake/情報制約回帰を維持。固定all-inだけではない通常preflop研究方策だが、全公開gameは解いていない。

HU private-vector+全rootsupportでは10秒で233k行以上に増え、1.5m行で約1.22GBを使った。QA約177MiB、予算は既存checkpoint保護のため100→128→256MiBへ明示改定、無料環境内。単純全サイズ/全stack構成の展開は現方式で現実的でない。20stack等の案を使った等stackだけでも2560game/14080position profile、最低1946880 RFI頻度行（既存承認案）。事前計算+digest付きcache+未資格cache miss局所計算が候補だが、正式品質での総計算量/保存量/cache miss時間/アプリ全体応答はUNKNOWN。Python行lookupを製品SLAとはしない。既知の品質FAIL方策を大量学習してその実測値を本番見積りに外挿しない。

## 再開・復元

元PRとGit上の実checkpointを読める環境へ復旧済み。source/build/native/prior SHAを照合。旧環境固有の未push/研究DB/ZIPの実バイトへはアクセスできず、復旧済みとは報告しない。Git保存成果から継続し、既存8候補/HU1BB/凍結CFRを変更していない。

active sourceは`integrated_final_study.py`、`integrated_solver.py`、`integrated_native.cc`。`support-preserved/{17120101,17120102}/{best,last}/checkpoint.*`が正規再開点。選択best(t0)と学習last(t43/t33)を区別。`replay-driver.py`で正規bestのstrict source/build/SHA/RNG復元後nextstep bytes一致を実測、receiptは`replay-and-last-coverage.json`。自動再開は実装していない。

ビルド準備（同じ無料環境、repository root）:

    python -B -m gto.qualification.build --directory /tmp/native-qualification
    python -B -c "from gto.qualification.sparse_solver import build; build('/tmp/sparse','/tmp/native-qualification')"
    python -B -c "from gto.qualification.integrated_solver import build; build('/tmp/integrated-v3','/tmp/native-qualification')"
    python -B -c "from gto.qualification.integrated_final_study import make; q,_,_,_=make(17120101,True); print(q.iteration,q.policy_digest)"

バイナリが異なればstrict復元は拒否する。元ビルドidentityを再現するか、raw/source/prior照合・明示migration・nextstep oracleを別証拠として保存する。identityだけ差し替えて再現済みとしない。古いv2/v3 sourceで生成した試験CPは対応snapshotのsourceでのみ復元する。現wrapperで歴史CPが自動再開できるとは主張しない。新trial出力guardがあるため既存folderへ学習再実行しない。

## 次工程・承認

formal12個別現値/依存/次工程は`acceptance.json`。全12false、前回比0。
次は同一solver内で過細分化の意味を保持した継続値/索引改善を最小単位で行い、独立BR・両seedの合法サイズ耐性・EV精度が改善する場合のみ拡大する。現在方式の無条件長時間学習は止める。完全BR/errorの計算経路が未成立なので発売可能との見積りは出せない。
正式20値(2,3,4,5,6,7,8,9,10,12,15,20,25,30,40,50,75,100,150,200BB)、全位置、MTT chipEV/ICM範囲、ring rake/cap/徴収条件、BBante0/.5/1、native格子外minraise/all-in、不均等vector、A7精度/必要証拠は既存`GTO_PREFLOP_RELEASE_APPROVAL_AND_EXECUTION_20261125.md`の承認待ちを維持。レビュー推奨はユーザー承認ではない。承認があっても品質UNKNOWNは解除されない。

本番DB/Storage/SQL/本番deploy/merge/SSO/課金/forcepush/成果削除なし。npm/build/lint/browserは今回offline Python/C++のみで適用外。CI SUCCESSは正式GTO品質PASSを意味しない。
