# 実測資源と初回版への適用限界

2CPU cgroup quota / RAM8GiB。Python3.12.14、NumPy2.3.5。
新方式もactive CFR+ private kernelを利用し、別solver方式へ切り替えていない。
全stack構成・全board・全合法historyの総当たり保存は採用しない。

- 3923node、13board、4,507,506 scalar cellsの同じindex作成比較:
  旧Python/copy経路13.062CPU秒（別測定17.547）、新batch特徴量/zero-copy1.831CPU秒。
  一回のCF更新は約6.322CPU秒。単一部品のbenchmarkで、solver全体やアプリSLAの
  7倍高速化と解釈しない。source-index-v1に旧経路を保存。
- 固定13board対照720CPU秒: seed1 t123/NC.399150、seed2 t138/NC.223040。
  fine BRは.846509/.961372。有限chance・限定actionでの結果であり、独立NLHではない。
- full52 streamingはboard/情報集合追加とCF積分時間を分離して保存。
  各seed最大64更新または1000純学習CPU秒、persistent scalar cap1000万。
  数値配列見積もり1.5GiB制限にはPython key metadataを含まず、実RSSも別測定。
  選択用NC32が16より5%以上改善し、同時paired逸脱の有意悪化がない時だけ64へ拡張。
  この研究gateは正式品質PASSではない。
- 新しいboard bankへの移行は旧R/Aを厳密に保持。異なるchance targetから移した
  warm behaviorに過去累積regretを偽って付与しない。
- lossless zstd shardは1blob100MiB未満。全過去checkpointを維持する保管費と、
  単一候補のserving artifact容量を分ける。artifact-identities.json参照。

初回版の事前計算＋資格済cache＋局所計算という構成は維持する。ただしcache miss
時に未資格の近似値を通常GTOとして返せる設計ではない。入力受理と品質合格は別。
20stack×8人数×(MTT1+ring7)×2ante=2560等stackprofileという旧案の下限を変えない。
位置・履歴・不均等stack・将来ICMはさらに別。2560は承認された正式profile数ではない。
たとえば各profile1000CPU秒という**精度保証のない単純予算例**でも256万CPU秒
(29.6CPU日)。これは必要計算量・完成予測・無料環境での達成可能性の証明ではない。
public抽象化/省略size/継続誤差を含む品質が未達のため、正式品質への必要反復数、
全初回版の保存量、資格済cache miss計算時間はUNKNOWN。

native独立評価・EV計算と復元の実測は各seed independent-final/に保存する。
Python内部row取得時間をアプリ全体検索応答時間と報告しない。
追加課金・環境増額は行っていない。
