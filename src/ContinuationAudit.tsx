import { useState } from 'react'
import { auditData, auditModels, findContinuationAudit } from './gto/continuationAudit'
import type { AuditStage } from './gto/continuationAudit'
import './ContinuationAudit.css'
const labels = { fixed_small: '元の小サイズ方策', fixed_large: '元の大サイズ方策', posterior_small: '到達レンジで再学習・小サイズ', posterior_large: '到達レンジで再学習・大サイズ', posterior_union: 'サイズ追加・2回レイズで再学習' }
export default function ContinuationAudit({ stage }: { stage: AuditStage }) {
 const [preflop, setPreflop] = useState('learned_small'), c = findContinuationAudit(stage, preflop)
 if (!c) return <section className="card gto-research" role="alert">継続モデル検証データが条件・品質情報と一致しません。結果を表示できません。</section>
 const gain = auditData.constructed_root_continuation_gains[preflop]
 const caller = stage === 'vs_3bet' ? '0' : '1', probability = c.root_call_probability
 return <section className="card gto-research gto-audit" aria-label="継続モデルの独立BR検証">
  <h2>研究用：継続モデルの独立BR検証</h2>
  <p><strong>実ゲームGTO精度は未検証です。</strong> プリフロップ方策を固定し、CALL後の継続ゲームで一方が応答を変えたときの利得を測っています。全ゲームGTOの誤差上限ではありません。</p>
  <label>固定するプリフロップ方策<select aria-label="固定するプリフロップ方策" value={preflop} onChange={e => setPreflop(e.target.value)}><option value="learned_small">小サイズ継続モデルで学習した方策</option><option value="learned_large">大サイズ継続モデルで学習した方策</option></select></label>
  <p>{stage === 'vs_3bet' ? '対3bet：SBが9BBまでコール' : '対4bet：BBが21BBまでコール'}。このCALL枝のルート到達確率：{(probability * 100).toFixed(4)}%。全{auditData.population.physical_flops.toLocaleString()}フロップを{auditData.population.orbits.toLocaleString()}同型代表で正しく加重しています。</p>
  <p>対3bet・対4betの2つのCALL枝で実際に構成した継続応答のルート改善利得：SB {gain.by_seat_bb['0'].toFixed(4)}／BB {gain.by_seat_bb['1'].toFixed(4)} BB、和 {gain.sum_bb.toFixed(4)} BB。これはプリフロップを変えずに見つかった利得で、全体の最大改善利得の上限ではありません。</p>
  <div className="gto-matrix-scroll" tabIndex={0} role="region" aria-label="継続モデルBR比較表"><table className="gto-audit-table"><caption>同じ到達レンジで比較。数値はCALL到達後の規定ゲーム内NashConv・BBです。</caption><thead><tr><th>継続方策</th><th>8特徴</th><th>本人169クラス追加</th><th>個別フロップも観測</th><th>CALLした側のモデルEV</th></tr></thead><tbody>
   {auditModels.map(name => { const m = c.models[name]; return <tr key={name} data-audit-model={name}><th>{labels[name]}</th><td>{m.texture_flags.conditional_call_nashconv_bb.toFixed(4)}</td><td>{m.texture_class_flags.conditional_call_nashconv_bb.toFixed(4)}</td><td>{m.board_class_flags.conditional_call_nashconv_bb.toFixed(4)}</td><td>{(m.by_seat[caller].texture_flags.profile_root_bb / probability).toFixed(4)}</td></tr> })}
  </tbody></table></div>
  <p>BRは相手のハンド分布を積分してから、本人のハンド情報と公開履歴で行動を選びます。相手の実際の非公開カードは使いません。NashConvは両者の一方的な改善利得の和です。</p>
  <details><summary>省略アクション・後続ストリートの未検証範囲</summary><p>追加モデルは0.1／0.25／1/3／1/2／3/4／1／2／10ポット（残りスタックで上限）とフロップ2回までのレイズを扱います。全合法サイズ・全ストリートのゲームではありません。再学習は固定プリフロップ到達レンジでの局所継続ゲームであり、プリフロップと継続方策を合わせた全体収束の証明ではありません。</p>
   {auditModels.map(name => { const e = c.models[name].future_street_envelope; return <p key={name}>{labels[name]}：後続ベットを未評価のショーダウン確率 {(e.unresolved_showdown_probability / probability * 100).toFixed(2)}%。その部分を±50BBで包絡したCALL後SB EV範囲 [{(e.root_lower / probability).toFixed(3)}, {(e.root_upper / probability).toFixed(3)}] BB。</p> })}
   <p>この包絡は安全な感度範囲で、実測した近似誤差や統計的信頼区間ではありません。ターン・リバーのショーダウンは990通りを列挙していますが、後続のベット判断は未評価です。外部GTO比較：未実施。正式受入0/12。通常GTOへの登録なし。</p>
  </details>
 </section>
}
