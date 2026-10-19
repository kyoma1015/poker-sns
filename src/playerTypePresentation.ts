export type ScoreDetail = {
  trait_scores: Record<string, number>
  discriminator_scores: Record<string, number>
}

const traitCopy: Record<string, { label: string; text: string }> = {
  initiative: { label: '自分から動く', text: '受け身で待つより、自分からアクションを起こして相手に判断を迫る傾向があります。' },
  risk_tolerance: { label: 'リスクを取れる', text: 'リスクがあること自体を理由に避けるより、見返りがあるなら踏み込める傾向があります。' },
  patience: { label: '待てる', text: 'すぐ結果を取りにいかず、より条件の良い場面まで待てる傾向があります。' },
  analytical: { label: '理屈から組み立てる', text: 'その場の印象だけでなく、レンジやアクションの流れを整理して判断する傾向があります。' },
  player_read: { label: '相手を見る', text: '一般論だけでなく、目の前の相手の反応や傾向を意思決定へ強く反映します。' },
  adaptability: { label: '戦い方を変えられる', text: '相手や卓の傾向が変われば、自分の基準に固執せず戦い方も変えられる側です。' },
  deception: { label: 'イメージを利用する', text: '相手が自分をどう見ているかまで考え、その予想を外す選択を使いやすい傾向があります。' },
  value_directness: { label: '取れる時に取り切る', text: '有利だと判断した場面では、回りくどくせず利益を取りにいく傾向があります。' },
  threat_sensitivity: { label: '危険信号を拾う', text: '状況が悪化したサインを軽視せず、損失が大きくなる前に警戒できる側です。' },
  novelty: { label: '新しい選択を試す', text: 'いつもの形だけに固定せず、新しい戦術やラインを試すことへの抵抗が小さい傾向があります。' },
  stability: { label: '基準がぶれにくい', text: '短期的な結果や空気に流されすぎず、自分の基準を保ちやすい傾向があります。' },
  confidence: { label: '判断を信じられる', text: '根拠を持って決めた後は、自分の判断を信じて実行しやすい側です。' },
  exploit: { label: '弱点を利益に変える', text: '相手の偏りやミスを見つけると、普段の戦い方から変えてでもそこを狙う傾向があります。' },
  tempo: { label: '反応が速い', text: '弱さや変化を感じたとき、様子見を長く続けるより早めにアクションへ移しやすい傾向があります。' },
  learning_receptivity: { label: '学びを取り込む', text: '自分だけの感覚に閉じず、他者の考えや新しい知識をプレーへ取り込みやすい側です。' },
  overview: { label: '卓全体を見る', text: '一人の相手だけでなく、テーブル全体の傾向や力関係まで見て判断する傾向があります。' },
  planning_horizon: { label: '先まで考える', text: '今の一手だけでなく、その後のストリートや展開まで見越してプランを作る傾向があります。' },
  history_use: { label: '過去の情報を使う', text: '以前のショーダウンや行動履歴を覚え、現在の判断材料として使いやすい側です。' },
  small_edge_accumulation: { label: '小さな利益を積む', text: '派手な一撃だけでなく、小さな有利を繰り返し拾うことを重視する傾向があります。' },
  action_efficiency: { label: '無駄な複雑さを減らす', text: '薄い利益のために難しい判断を増やすより、効率の良い場面へ集中する傾向があります。' },
  interaction_read: { label: '相手との読み合いを見る', text: '自分と相手の間で起きている読み合いや、相手からの見られ方を判断へ反映しやすい側です。' },
  pressure_resistance: { label: '圧力に崩れにくい', text: '強いベットやプレッシャーを受けても、それだけで判断を曲げにくい傾向があります。' },
  independent_judgment: { label: '自分の根拠で決める', text: '周囲と意見が違っても、自分なりの根拠があるなら判断を保てる側です。' },
  selective_burst: { label: '勝負所で一気に行く', text: '常に攻め続けるより、ここだと判断した場面で攻撃量を大きく上げる傾向があります。' },
  pot_size_comfort: { label: '大きなポットを怖がらない', text: 'ポットが大きくなること自体には過度に萎縮せず、必要なら大きな勝負へ入れる側です。' },
  fun_orientation: { label: '面白さも大事にする', text: '利益だけでなく「この展開をやってみたい」という面白さも意思決定へ入りやすい傾向があります。' },
  attack_momentum: { label: '攻めの流れを続ける', text: '一度作った攻撃の流れを簡単には手放さず、継続して圧力をかけやすい側です。' },
  balance_awareness: { label: '偏りすぎを避ける', text: '相手に簡単に対応されないよう、自分のベットやレイズの頻度が偏りすぎないことを意識する傾向があります。' },
  retreat_response: { label: '危険なら引き返せる', text: '途中で状況が悪化したと判断すれば、最初のプランに固執せず撤退へ切り替えられる側です。' },
  improvisation: { label: 'その場で組み直せる', text: '予定外の展開でも、その場で増えた情報を使って新しいプランを作り直す傾向があります。' },
  stimulus_orientation: { label: '動きのある展開を好む', text: '静かに待ち続けるより、判断やアクションが多い展開に入りやすい傾向があります。' },
  collision_avoidance: { label: '難しい衝突を避ける', text: '利益がありそうでも、後で大きく難しい衝突になりやすいなら最初から見送る傾向があります。' },
}

// Positive score ceilings from the audited 50-question option bank.
// Compare tendencies on the same relative scale, not by raw point totals.
export const traitPositiveMax: Record<string, number> = {
  initiative: 19, risk_tolerance: 4, patience: 23, analytical: 26,
  player_read: 14, adaptability: 28, deception: 10, value_directness: 10,
  threat_sensitivity: 20, novelty: 16, stability: 28, confidence: 11,
  exploit: 48, tempo: 12, learning_receptivity: 7, overview: 14,
  planning_horizon: 12, history_use: 25, small_edge_accumulation: 11,
  action_efficiency: 20, interaction_read: 25, pressure_resistance: 10,
  independent_judgment: 8, selective_burst: 9, pot_size_comfort: 9,
  fun_orientation: 27, attack_momentum: 15, balance_awareness: 19,
  retreat_response: 9, improvisation: 8, stimulus_orientation: 6,
  collision_avoidance: 7,
}
export function relativePositiveScore(key: string, score: number): number {
  const cap = traitPositiveMax[key]
  return cap && Number.isFinite(score) ? Math.max(0, Math.min(1, score / cap)) : 0
}

export function topPersonalTraits(detail: ScoreDetail) {
  const all = { ...detail.trait_scores, ...detail.discriminator_scores }
  return Object.entries(all)
    .filter(([key, value]) => traitCopy[key] && Number.isFinite(Number(value)) && Number(value) > 0)
    .sort((a, b) => relativePositiveScore(b[0], Number(b[1])) - relativePositiveScore(a[0], Number(a[1])))
    .slice(0, 3)
    .map(([key]) => ({ key, ...traitCopy[key] }))
}

// These thresholds select wording, not skill ratings or animal classification.
// At least 40% of the positive scale is required before asserting a tendency.
export function personalAdvice(detail: ScoreDetail) {
  const scores = { ...detail.trait_scores, ...detail.discriminator_scores }
  const raw = (key: string) => Number(scores[key] ?? 0)
  const relative = (key: string) => relativePositiveScore(key, raw(key))

  if (relative('initiative') >= 0.45 && relative('confidence') >= 0.3 &&
      raw('threat_sensitivity') <= 0 && relative('attack_momentum') >= 0.4) {
    return '自分から動き、攻めを続ける回答が目立ちます。相手やボードが変わったら、ベットを続ける理由が今もあるか確認してみましょう。'
  }
  if (relative('exploit') >= 0.4 && relative('adaptability') >= 0.4) {
    return '相手に合わせて戦い方を変える回答が目立ちます。少ない回数の観察だけで相手の傾向を決めつけていないか、調整の根拠を振り返ってみましょう。'
  }
  if (relative('analytical') >= 0.4 && raw('action_efficiency') < 0) {
    return '理由を整理して考える回答が目立ちます。判断が複雑になったときは、重要な情報と結論を一度短く整理してみましょう。'
  }
  if (relative('fun_orientation') >= 0.4 && relative('risk_tolerance') >= 0.4) {
    return '面白さを重視し、リスクを取る回答が目立ちます。参加する前に、楽しさと期待できる利益をそれぞれ確認してみましょう。'
  }
  if (relative('attack_momentum') >= 0.4 && relative('initiative') >= 0.45 && raw('adaptability') <= 0) {
    return '攻めを続ける回答が目立ちます。途中で状況が変わったときは、最初のプランにこだわらず、チェックやフォールドも含めて考え直してみましょう。'
  }
  if (relative('patience') >= 0.4 && relative('selective_burst') >= 0.4 &&
      relative('confidence') >= 0.3 && raw('attack_momentum') >= 0) {
    return '機会を待ち、条件がそろった場面で攻める回答が目立ちます。待つ理由と攻める理由をそれぞれ言葉にして振り返ってみましょう。'
  }
  if (relative('threat_sensitivity') >= 0.4 || relative('collision_avoidance') >= 0.4) {
    return '危険のサインや難しい衝突を意識する回答が目立ちます。参加を続ける場合も降りる場合も、相手の行動やポットの状況を確認し、選ぶ理由を整理してみましょう。'
  }
  return '回答だけで実戦の強さは判断できません。最近のハンドを一つ選び、参加・ベット・コール・フォールドを選んだ理由と、その後に得た情報を振り返ってみましょう。'
}
