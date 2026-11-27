# 根本監査と公開研究の照合（2026-11-26）

以下は公開論文の適用条件の比較であり、Poker IDの実測値ではない。商用GTOデータ取得、契約、スクレイピングは行っていない。外部コードの転載・依存追加なし。

| 方式・一次資料 | 条件と今回の差 | 資源・実装判断 |
|---|---|---|
| [MCCFR, Lanctot et al. 2009](https://proceedings.neurips.cc/paper/2009/hash/00411460f7c92d2124a67ea0f4cb5f85-Abstract.html) | 不偏counterfactual推定、正のsampling support、適切なregret matchingと平均。2p zero-sumの平均戦略保証を多人数のproduct Nashへ拡張しない | 既存native samplerを維持。signed regretとuniform averageを比較可能にした。未知サイズ/抽象化誤差が消える定理ではない |
| [PCS, Johanson et al. 2012](https://bowlingmh.github.io/publications/b2hd-12aamas-pcs.html) | 公開chanceのみsampleしprivate積分を共有。今回の全private積分は一致するが、未来public actionもsampleするため完全PCSではない | rank-prefix/card removalを再利用。public historyの分岐数とimportance weightは別問題 |
| [CFR+, Tammelin 2014](https://arxiv.org/abs/1407.5042) | regret matching+、clip、重み付き平均。完全列挙の高速性を高分散samplingへ無条件に持ち込めない | E[max(0,R+g)] != max(0,R+E[g])。raw不偏性のテストだけではsampling後clipの品質を証明しない |
| [VR-MCCFR, Schmid et al.](https://arxiv.org/abs/1809.03057) | action baselineの重要度補正により、baselineが不正確でも適切な条件下で不偏性を維持 | 今回の第一実装。current range/private vector/native passive rolloutを**学習用control variateだけ**に使い、実際の継続方策をpassiveへ変更しない。方策への未来board入力は禁止のまま |
| [DCFR, Brown/Sandholm 2019](https://www.cs.cmu.edu/~sandholm/cs15-888F21/reweighting.aaai19.pdf) | 正負regret/平均のdiscount等。各variantのsampling/pruning適合は同じではない | discountを追加して原因を隠さず、まず既存更新器の不偏性・clip分散・warm量を分離。今回はDCFRを採用しない |
| [Deep CFR 2019](https://proceedings.mlr.press/v97/brown19b.html) | regret/value近似誤差とsampling誤差がある。表の行共有率をNN品質へ置換できない | 3CPUの現環境で再学習データ・NN誤差証明・時間が未実測。新しいML依存/巨大bufferを先行導入しない |
| [Depth-limited solving 2018](https://arxiv.org/abs/1805.08195) | 不完全情報では単一の固定leaf EVだけでは不十分。相手の継続選択とrangesが重要 | 全stack列挙を避ける候補。ただしrange固定payoff問題を繰り返さず、同一ゲームのcontinuation/error envelopeが必要 |
| [DeepStack / continual resolving](https://arxiv.org/abs/1701.01724) / [ReBeL](https://arxiv.org/abs/2007.13544) | public belief/range、相手CF値、安全な境界/近似誤差条件が必要。一般の多人Nash保証ではない | precompute+cache+local solvingの設計候補。未検証leaf networkや未知のopponent CF上界を資格証明に使わない |
| [OpenSpiel](https://github.com/google-deepmind/open_spiel) / [LICENSE](https://github.com/google-deepmind/open_spiel/blob/master/LICENSE) | Apache-2.0。CFR/external samplingの公開実装を照合可能。商用戦略データではない | native coreを置換せず方式と平均/reachの参照に使用。コードを取り込む場合はpin/NOTICE等を別途維持。今回はコード転載なし |

## 確認した式・実装上の機構

現在のfull-board draw下でprivate pair lawは各1070190合法ordered pairへ一様。
CF値は相手の到達率を積分し、owner到達率を掛けない。owner reachはaverageにのみ使う。public action prefixのproposalをq_prefix、選択action確率をq_aとすると、raw推定値に1/(q_prefix*q_a)補正が必要。root全support列挙ではroot proposalを消す。両ownerは同じpreupdate方策を使う。

baseline修正は `vhat_a=b_a+1[A=a]*(vhat_child-b_a)/q_a`。owner節点はπ加重、opponent節点は相手πを含むrangeを加算する。baselineは選択前に各actionで定義し、sampled future rolloutがpolicy keyへ流れない。全pathの期待値を独立dense oracleと比較する。

旧warmのroot保存行は86/169、81/169。保存行のold R/Aと未保存行のR=1e-6/A=1e-3は異なる擬似標本量で、学習current R方策と報告A方策も同じではない。これは原checkpointを破壊せず新gameの初期化として分離する問題。全行を同一擬似量へ再baseしてもseed1の品質は改善しなかったため、単独原因・採用修正と断定しない。

旧43更新の428879行のうちregret更新済み234390行。opponentを読むだけのprior-only行を永続化していた。新lazy allocationはそれを一時mapに置き、更新行R/A・RNGが元実装と完全一致することを試験する。単純なrow cap引上げではない。

## 評価ゲームと証明経路

884ノード・固定2boardのNCは、full方策を制限actionへ条件付けした**別の有限ゲーム**。除外確率も保存する。full-native NC/BR上界ではない。キーを粗くした候補のBR能力まで制限すると品質比較が不公平になるため、新対照実験のprimary BRは全候補共通のown exact hole+visible public boardで行う。未来boardはBR情報集合にも渡さない。有限board lawからprivate cardsを通じて得られる情報はこの人工gameの性質で、実native chance lawと同じとは主張しない。

2p zero-sumで同じmapped policy/gameを比較し、全継続戦略に一様なpayoff誤差ε、chance一様誤差η、追加サイズ/情報の一方逸脱利得上界δ_i、κ_iが証明できるなら、
`NC_native <= NC_reduced + 2(ε+η) + δ_0+δ_1+κ_0+κ_1`。
δ_i/κ_iは同じmapped opponent方策を固定したネスト状のgame refinement chainで、各段階の追加BR差を順に上界にする必要がある。異なるgameで別々に測った平均gainを単に足してはいけない。
`integrated_br.transfer_bound`は必要な上界がUNKNOWNなら数値を返さない。on-policy EVの狭い区間は、一様なBR継続誤差ではない。

完全有限ゲーム上で応答pure戦略数M、utility range L、独立chance標本nに対する一様Hoeffding補正は `L sqrt((log(2M/δ))/(2n))` が一つの保守的経路。log Mは全応答情報集合のlog(action数)の合計で、未学習行を除外してはいけない。既知行だけを用いた数は完全証明ではない。例えばlog M=100000、L=100BB、ε=.05BBでもn約2e11で、この保守的routeは無料環境で現実的でない。これは全アルゴリズムの必要時間下限ではない。

native全chance・全合法サイズのBRを厳密列挙する代わりに、interval branch-and-bound、同一range下のsafe subgame CF上界、uniform continuation envelopesで未展開部分を覆う経路を調査した。ただし現実装ではδ_i/κ_i/ε/ηを証明できずUNKNOWN。物理的100BBを収束証拠としない。
