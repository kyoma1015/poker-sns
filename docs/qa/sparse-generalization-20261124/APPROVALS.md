# 正式profile承認待ち一覧（未採用）
既存docs/specs/GTO_PREFLOP_RELEASE_PROPOSAL_20261117.mdを整理。全案未承認。
研究用条件と正式仕様を混同せず、承認待ちで承認不要の開発を停止しない。
正式受入12条件・2〜9人・複数stack・全位置・不均等stack等を除外しない。

| 項目 | 既存推奨案／選択肢 | 理由・未確定範囲 |
|---|---|---|
| 20stack | 推奨A:2,3,4,5,6,7,8,9,10,12,15,20,25,30,40,50,75,100,150,200BB。代替は原文中深度案／原典回収 | short/deepと既存研究を含む。原典回復・正式採用済みではない |
| サイズ | 推奨B1:0.5BBchipの全native合法raise-to。代替B2:0.25BB、B3:疎な学習+全size誤差上界 | 既存native再利用。B3でも全逸脱の精度要件は消えない |
| MTT/ring | MTTchipEV案とring案を分離。ICM範囲も承認対象 | chipEV限定を正式MTT全体として勝手に採用しない |
| ante | 既存案BBante0/1BB、ante-first等。方式・支払基準の採否 | 実ゲーム条件一致が必要。研究のante0/1BBは正式値ではない |
| rake | 既存ring7案:0%、5%/10%各capなし/5/10BB。徴収/丸め等も未承認 | house rulesでEVが変わるため明示profileが必要 |
| 不均等stack | 20等stack表と別に配置matrixを承認。研究例50/40/30BB循環は一例 | 全席のshortallin/sidepot/返金条件を除外しない。正式matrix原典不足 |
| 品質具体値 | 既存C案の一方逸脱.05BB、HU NC.1BB、EVhalfwidth.05BB/99.9%等は草案 | 新規数値を正式基準と断定しない。12条件は維持、未知をPASSにしない |

今回研究:HU50 ante/rake0。N6/9は50/40/30BB循環、BBante1BB、rake5%。
これらの研究設定を正式profileへ登録していない。初回版をHU50へ縮小しない。
