import { useState } from 'react'
import { handGrid } from './gto/rangeCatalog'
import { independentResearch as data, histories } from './gto/independentResearch'
import type { IndependentStage } from './gto/independentResearch'

const colors = ['#586273', '#167aa4', '#9d3f73']
const names: Record<string, string> = { fold: 'フォールド', call: 'コール', raise_to_5: '2.5BBへレイズ', raise_to_18: '9BBへ3ベット', raise_to_42: '21BBへ4ベット', raise_to_100: '50BBオールイン' }
const pair = (xs: number[]) => xs.map(x => x.toFixed(3)).join(', ')
function background(xs: number[]) { let total = 0; return `linear-gradient(90deg,${xs.map((x, i) => { const before = total; total += x * 100; return `${colors[i]} ${before}% ${total}%` }).join(',')})` }
export default function IndependentPreflop({ stage }: { stage: IndependentStage }) {
  const [variant, setVariant] = useState('learned_small')
  const [hand, setHand] = useState('AA')
  const model = data.models[variant], context = model.contexts[stage], row = context.hands[hand]
  const sample = data.oracle_summary.evaluation_oracle
  const exact = data.uncertainty_kind === 'enumerated_population_with_empirical_rounding_guard'
  return <section className="card gto-research" aria-label="独立学習プリフロップ研究版">
    <h2>独立学習プリフロップ研究版</h2>
    <p role="note"><strong>研究版／実戦GTO精度未検証</strong>。通常GTOの合格データではありません。</p>
    <p>HU50BB・アンティ／レーキなし・MTTはchipEV。サイズ2.5／9／21／50BB。公開履歴：{histories[stage]}。{context.actor === 0 ? 'SB' : 'BB'}の169ハンドを表示します。</p>
    <label>独立学習の継続モデル<select aria-label="独立学習の継続モデル" value={variant} onChange={e => setVariant(e.target.value)}>
      <option value="learned_small">小サイズ：1/3・1/2・3/4ポット</option><option value="learned_large">大サイズ：1/2・1・2ポット</option>
    </select></label>
    <p>フロップの学習方策を固定し、全プリフロップ分岐を一貫したゲームとして学習。フロップは1回のベットと応答まで、後続ストリートはチェックで進む近似モデルです。相手の実際の非公開カードは判断に使いません。</p>
    <p>学習利得表内NashConv：{model.sample_game_nashconv_bb.toFixed(6)} BB。{exact ? '全列挙した固定モデル内の評価' : '独立評価標本'}：{model.evaluation_sample_nashconv_bb.toFixed(6)} BB。固定継続モデルの期待ゲームに対する{exact ? '数値ガード付きNashConv区間' : 'NashConv区間'}：[{pair(model.root_expected_game_bounds_bb.preflop_nashconv_interval)}] BB。</p>
    <p>{data.quality.expected_game_root_NC_upper_at_most0_1 ? 'この固定継続モデルの計算値は研究上の0.1BB基準を満たしました。' : '期待ゲームの0.1BB収束基準は未達です。'} 実ゲームの近似誤差UNKNOWN、外部GTO比較未実施です。</p>
    <div className="gto-legend">{context.actions.map((a, i) => <span key={a}><i style={{ background: colors[i] }} />{names[a]}</span>)}</div>
    <div className="gto-matrix-scroll" tabIndex={0} role="region" aria-label="独立学習169ハンド表">
      <table className="gto-matrix"><caption>研究用の混合頻度・モデルEV（通常GTOではありません）</caption>
        <tbody>{handGrid.map((r, i) => <tr key={i}>{r.map(label => <td key={label}>
          <button type="button" data-independent-hand={label} aria-pressed={hand === label} aria-label={`独立学習 ${label}`} style={{ background: background(context.hands[label].frequencies) }} onClick={() => setHand(label)}><strong>{label}</strong><small>{context.hands[label].ev_bb.toFixed(2)} BB</small></button>
        </td>)}</tr>)}</tbody>
      </table>
    </div>
    <section aria-live="polite" data-independent-detail><h3>{hand}：独立学習の頻度・EV</h3>
      <ul>{context.actions.map((a, i) => <li key={a}>{names[a]}：{(row.frequencies[i] * 100).toFixed(1)}%／モデルEV {row.action_ev_bb[i].toFixed(3)} BB／区間 [{pair(row.action_ev_intervals_bb[i])}] BB</li>)}</ul>
      <p>混合方策EV：{row.ev_bb.toFixed(3)} BB／区間 [{pair(row.model_ev_interval_bb)}] BB。ブラインド支出を含む純損益です。</p>
    </section>
    <details><summary>計算範囲・誤差・再現性</summary>
      <p>169/169ハンド×4局面×2モデル。各フロップの合法ホールカード対とターン・リバー990通りを列挙。</p>
      {exact ? <p>スート名に依存しないこの固定モデルでは、{sample.unique_physical_flops}代表フロップを同型数で重み付けし、全{sample.represented_physical_flops?.toLocaleString()}フロップの期待値を集計しています。カード除去・公開履歴・到達レンジを保持。有限母集団の標本誤差は0ですが、継続モデルの近似誤差は残ります。</p>
        : <p>フロップ母集団22,100枚組の積分はサンプリングで、独立評価{sample.samples}標本・実計算{sample.unique_physical_flops}ボード（{(sample.exact_board_fraction * 100).toFixed(3)}%）。推定器の全枝対応は完全全列挙の意味ではありません。</p>}
      {exact ? <p>表示区間は各終端利得の数値ガード1e-7BBから伝播した値です。統計的信頼区間ではなく、形式的な丸め誤差証明でもありません。</p> : <p>表示区間は学習・独立評価の両利得表を合わせ同時99%です。</p>}
      <p>継続モデル近似誤差・外部GTO偏差は含みません。2モデルの差はサイズ感度であり、正解との誤差ではありません。</p>
      <p>元の凍結CFRと研究版8レンジを変更せず、{exact ? '新しい方策は同じ完全利得表で学習・BR評価したモデル内の結果です。独立した実ゲーム検証ではありません。' : '新しい方策を評価データの参照前に固定しています。'}正式受入0/12。</p>
      <p className="gto-digest">方策：{model.policy_digest}／事前登録：{data.protocol_sha256}</p>
    </details>
  </section>
}
