# 未承認の正式仕様（変更・採用なし）

原本: docs/specs/GTO_PREFLOP_RELEASE_APPROVAL_AND_EXECUTION_20261125.md。
今回のfull52/HU50/13board/CDF/nativeサイズは隔離研究条件。正式仕様ではない。

- A1 20stack案: 2,3,4,5,6,7,8,9,10,12,15,20,25,30,40,50,75,100,150,200BB。
- A2 2〜9人・全位置、既存位置表を維持。
- A3 .5BB格子全native合法raise-to＋格子外の合法最小raise/all-in/shortall-in。
  代表表示RFI2/2.5/3/3.5、3bet8/8.5/9/10/10.5、4bet20/21/22BB＋jam。
  研究support12/99は正式サイズ制限の承認案ではない。
- A4 MTT chipEV＋ring案M1 / ICMを含むM2 / 保留。ICM既定要件を勝手に除外しない。
- A5 原案BBante0/1BB、ring0%または5%/10%、capなし/5/10BB等は引き続き未承認。
  レビュー側のBBante.5、現実的rake/cap再評価提案も正式承認ではない。
  no-flop-no-drop/丸め/徴収時点をidentityへ含め、profileを混同しない。
- A6 実stack vector入力、各.5〜200BB/.5BB格子という原案。effective stackへ
  一括丸めない。最低検証族は全域精度証明ではない。
- A7 原案各playerの完全BR gain上界≤.05BB/hand、HU NC上界≤.1BB、
  全169/表示actionの条件付きEV halfwidth≤.05BB/family confidence≥99.9%。
  未承認閾値への到達を正式合格と呼ばず、原案の閾値を緩和しない。

承認前でも、正しいchance/reach/card removal、native合法応答、共同CFR、独立BR、
全169/各action推定、多人数精算/情報制約、復旧可能なcheckpointは開発できる。
未承認を理由にそれらを停止していない。一方、具体値の正式profile採用と
通常registry公開は現時点で行わない。正式受入12条件はacceptance.jsonに維持。
