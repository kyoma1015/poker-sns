import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { canonicalQuery, findVerifiedRange, handGrid, oneBBQuery, positions } from './gto/rangeCatalog'
import type { RangeQuery, ReviewedCertificate, VerifiedRange } from './gto/rangeCatalog'
import { reviewedCertificates, verifiedCatalog } from './gto/verifiedCatalog'
import { abstractResearch, abstractResearchQuery, findAbstractResearch } from './gto/abstractResearch'
import type { AbstractStage } from './gto/abstractResearch'
import './GtoPreflop.css'

const stages = { rfi: 'RFI（自分まで全員フォールド）', vs_open: 'オープンへの対応',
  vs_3bet: '3ベットへの対応', vs_4bet: '4ベットへの対応', forced_blind_allin: '検証用：HU1BB・BB強制オールインへの対応' }
const colors = ['#586273', '#167aa4', '#9d3f73', '#82702e', '#4454a8', '#25744f']
const initialQuery: RangeQuery = { format: 'mtt', players: 6, seat: 2, stackBb: '', anteBb: '0',
  rakePct: '0', rakeCapBb: null, openBb: '', threeBetBb: '', fourBetBb: '', stage: 'rfi' }
function bar(frequencies: number[]): string {
  let total = 0
  return `linear-gradient(90deg, ${frequencies.map((frequency, index) => {
    const before = total; total += frequency * 100
    return `${colors[index % colors.length]} ${before}% ${total}%`
  }).join(', ')})`
}
type Props = { catalog?: readonly unknown[]; certificates?: Readonly<Record<string, ReviewedCertificate>> }

export default function GtoPreflop({ catalog = verifiedCatalog, certificates = reviewedCertificates }: Props) {
  const navigate = useNavigate()
  const [form, setForm] = useState<RangeQuery>(initialQuery)
  const [result, setResult] = useState<VerifiedRange | null>(null)
  const [message, setMessage] = useState('条件を入力して検索してください。')
  const [error, setError] = useState('')
  const [selected, setSelected] = useState('AA')
  const [researchOptIn, setResearchOptIn] = useState(false)
  const [researchStage, setResearchStage] = useState<AbstractStage | null>(null)
  const isForced = form.stage === 'forced_blind_allin'
  const hasOneBB = findVerifiedRange(oneBBQuery, catalog, certificates) !== null
  function change(patch: Partial<RangeQuery>) {
    setForm(previous => ({ ...previous, ...patch }))
    setResearchStage(null); setResult(null); setError(''); setMessage('条件を入力して検索してください。')
  }
  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      const query = canonicalQuery(form)
      const match = findVerifiedRange(query, catalog, certificates)
      setResearchStage(researchOptIn ? findAbstractResearch(query) : null)
      setResult(match); setSelected('AA'); setError('')
      setMessage(match ? '計算条件と検証根拠が一致するデータを表示しています。' : 'この条件の検証済みデータはまだありません。')
    } catch (caught) {
      setResearchStage(null); setResult(null); setError(caught instanceof Error ? caught.message : '検索条件を確認してください。')
    }
  }
  const selectedRow = result?.hands[selected]
  return (
    <main className="app gto-preflop">
      <section className="card">
        <button className="gto-back" type="button" onClick={() => navigate('/tools')}>← ポーカーツール</button>
        <h1>プリフロップレンジ検索</h1>
        <p className="gto-intro">検証済みの条件を完全一致で検索します。未計算・未検証の条件を補間して表示しません。</p>
        {catalog.length === 0 && <p className="gto-notice">検証済みレンジデータは準備中です。条件を指定できますが、現在表示できるGTO戦略はありません。</p>}
        {hasOneBB && <aside className="gto-notice">
          <p>明示的な検証用条件として、HU・両者1BBのレンジを利用できます。通常のRFIオープンや3ベットの代用ではなく、正式20スタック条件のデータではありません。</p>
          <button className="gto-preset" type="button" onClick={() => change(oneBBQuery)}>検証済みテスト条件：HU1BB</button>
        </aside>}
        <aside className="gto-notice">
          <p>HU50BBの抽象化モデルを研究用に比較できます。実ゲームのGTO精度は未検証で、正式GTOレンジには含めていません。</p>
          <button type="button" onClick={() => { change(abstractResearchQuery); setResearchOptIn(true) }}>研究用：HU50BB抽象化モデル</button>
        </aside>
        <form aria-label="プリフロップ検索条件" onSubmit={search}>
          <label><input type="checkbox" checked={researchOptIn} onChange={event => { setResearchOptIn(event.target.checked); setResearchStage(null) }} />抽象化モデルの研究結果も確認する（実ゲームGTO未検証）</label>
          <fieldset className="gto-fields"><legend>計算条件</legend>
            <label>ゲーム形式<select aria-label="ゲーム形式" disabled={isForced} value={form.format} onChange={event => change({ format: event.target.value as RangeQuery['format'], rakePct: '0', rakeCapBb: null })}>
              <option value="mtt">MTT（chipEV）</option><option value="ring">リングゲーム</option>
            </select></label>
            <label>人数<select aria-label="人数" disabled={isForced} value={form.players} onChange={event => {
              const players = Number(event.target.value); change({ players, seat: positions(players)[0].seat })
            }}>{Array.from({ length: 8 }, (_, i) => i + 2).map(n => <option key={n} value={n}>{n}人</option>)}</select></label>
            <label>ポジション<select aria-label="ポジション" disabled={isForced} value={form.seat} onChange={event => change({ seat: Number(event.target.value) })}>
              {positions(form.players).map(position => <option key={position.seat} value={position.seat}>{position.label}</option>)}
            </select></label>
            <label>有効スタック（BB）<input aria-label="有効スタック（BB）" disabled={isForced} required inputMode="decimal" value={form.stackBb} placeholder="例：100" onChange={event => change({ stackBb: event.target.value })} /></label>
            <label>BBアンティ<select aria-label="BBアンティ" disabled={isForced} value={form.anteBb} onChange={event => change({ anteBb: event.target.value as RangeQuery['anteBb'] })}>
              <option value="0">なし</option><option value="1">1 BB</option>
            </select></label>
            <label>レーキ<select aria-label="レーキ" disabled={isForced || form.format === 'mtt'} value={form.rakePct} onChange={event => change({ rakePct: event.target.value as RangeQuery['rakePct'] })}>
              <option value="0">0%</option><option value="5">5%</option><option value="10">10%</option>
            </select></label>
            <label>レーキ上限<select aria-label="レーキ上限" disabled={isForced || form.format === 'mtt'} value={form.rakeCapBb ?? 'none'} onChange={event => change({ rakeCapBb: event.target.value === 'none' ? null : event.target.value as '5' | '10' })}>
              <option value="none">上限なし</option><option value="5">5 BB</option><option value="10">10 BB</option>
            </select></label>
            <label>オープンサイズ（BB）<input aria-label="オープンサイズ（BB）" disabled={isForced} required={!isForced} inputMode="decimal" value={form.openBb ?? ''} placeholder={isForced ? '適用なし' : '合計額'} onChange={event => change({ openBb: event.target.value })} /></label>
            <label>3ベットサイズ（BB）<input aria-label="3ベットサイズ（BB）" disabled={isForced} required={!isForced} inputMode="decimal" value={form.threeBetBb ?? ''} placeholder={isForced ? '適用なし' : '合計額'} onChange={event => change({ threeBetBb: event.target.value })} /></label>
            <label>4ベットサイズ（BB）<input aria-label="4ベットサイズ（BB）" disabled={isForced} required={!isForced} inputMode="decimal" value={form.fourBetBb ?? ''} placeholder={isForced ? '適用なし' : '合計額'} onChange={event => change({ fourBetBb: event.target.value })} /></label>
            <label className="gto-wide">対象局面<select aria-label="対象局面" value={form.stage} onChange={event => {
              const stage = event.target.value as RangeQuery['stage']
              change(stage === 'forced_blind_allin' ? oneBBQuery : isForced ? { stage, openBb: '', threeBetBb: '', fourBetBb: '' } : { stage })
            }}>
              {Object.entries(stages).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
            </select></label>
          </fieldset>
          <button className="gto-search" type="submit">検証済みレンジを検索</button>
        </form>
        {error && <p role="alert" className="gto-error">{error}</p>}
        <p role="status" className="gto-status">{message}</p>
        {result?.conditionClass === 'explicit_test' && <p className="gto-notice">{result.conditionName}。正式仕様のデータとは別の明示テスト条件です。</p>}
        <h2 id="gto-matrix-title">169ハンド表</h2>
        <p className="gto-intro">スーテッドは右上、オフスートは左下。空欄は未提供を表し、フォールド頻度0%を意味しません。</p>
        {result && <div className="gto-legend">{result.actions.map((action, i) => <span key={action}><i style={{ background: colors[i % colors.length] }} />{action}</span>)}</div>}
        <div className="gto-matrix-scroll" tabIndex={0} role="region" aria-labelledby="gto-matrix-title">
          <table className="gto-matrix" aria-label="169ハンドレンジ表">
            <caption>{result ? '169 / 169ハンド、1326 / 1326コンビネーション。セルを選ぶと頻度とEVを確認できます。' : '検証済みデータ未提供：頻度・EVは表示していません。'}</caption>
            <thead><tr><th scope="col" aria-label="ハンド" />{Array.from('AKQJT98765432').map(rank => <th scope="col" key={rank}>{rank}</th>)}</tr></thead>
            <tbody>{handGrid.map((row, index) => <tr key={index}>
              <th scope="row">{'AKQJT98765432'[index]}</th>
              {row.map(label => {
                const data = result?.hands[label]
                return <td key={label}><button type="button" data-hand={label} disabled={!data} aria-pressed={selected === label && Boolean(data)}
                  aria-label={`${label}${data ? ` EV ${data.evBb.toFixed(3)} BB` : ' 未提供'}`}
                  style={data ? { background: bar(data.frequencies) } : undefined} onClick={() => setSelected(label)}>
                  <strong>{label}</strong><small>{data ? `${data.evBb.toFixed(3)} BB` : '—'}</small>
                </button></td>
              })}
            </tr>)}</tbody>
          </table>
        </div>
        {result && selectedRow && <section className="gto-detail" aria-live="polite">
          <h2>{selected}の頻度とEV</h2>
          <ul>{result.actions.map((action, i) => <li key={action}>{action}：{(selectedRow.frequencies[i] * 100).toFixed(1)}%</li>)}</ul>
          <p>EV：{selectedRow.evBb.toFixed(3)} BB{result.certificate.verificationMethod === 'simultaneous_full_game_action_bounds' ? '（推定値）' : ''}</p>
          <p>EV同時区間：[{selectedRow.evIntervalBb[0].toFixed(3)}, {selectedRow.evIntervalBb[1].toFixed(3)}] BB</p>
          <p>検証信頼水準：{(result.certificate.confidence * 100).toFixed(result.certificate.confidence === 1 ? 0 : 7)}%</p>
          {result.certificate.samplingAssumptions && <p>{result.certificate.samplingAssumptions}</p>}
          <p>Coverage：169 / 169ハンド・1326 / 1326コンビネーション</p>
          <details><summary>計算条件と収束の検証根拠</summary>
            <p>対象ゲーム全体の一方的な戦略変更による利得上限：{result.certificate.upperBoundBb} BB</p>
            <p>検証時の許容値：{result.certificate.acceptedToleranceBb} BB</p>
            <p>根拠：{result.certificate.reviewReference}</p>
            {result.certificate.policyConstruction && <p>{result.certificate.policyConstruction}</p>}
            {result.certificate.directHeroRepresentatives && <p>直接評価：{result.certificate.directHeroRepresentatives}代表クラス。スート・配布順の対称性による展開：{result.certificate.symmetryExpandedCombinations}コンビネーション／{result.certificate.strategicInformationSets}情報集合。</p>}
            <p>ポリシー：{result.policyDigest}</p><p>計算条件：{result.configDigest}</p>
            <p>研究用の局所指標やEVサンプリング誤差を、ゲーム全体の収束根拠として使用していません。</p>
          </details>
        </section>}
      </section>
      {researchStage && <AbstractResearchPanel key={researchStage} stage={researchStage} />}
    </main>
  )
}

function AbstractResearchPanel({ stage }: { stage: AbstractStage }) {
  const [mode, setMode] = useState<'checkdown' | 'flop_controller'>('flop_controller')
  const [hand, setHand] = useState('AA')
  const model = abstractResearch.models[mode]
  const context = model.contexts[stage]
  const hands = context.hands as Record<string, { frequencies: number[]; ev_bb: number; action_ev_bb: number[]; model_ev_interval_bb: number[] }>
  const selected = hands[hand]
  const sensitivity = abstractResearch.independent_seed_comparison.find(row => row.mode === mode && row.stage === stage)
  const names: Record<string, string> = { fold: 'フォールド', call: 'コール', check: 'チェック', raise_to_5: '2.5BBへレイズ', raise_to_18: '9BBへレイズ', raise_to_42: '21BBへレイズ', raise_to_100: '50BBオールイン' }
  return <section className="card gto-research" aria-label="抽象化モデルの研究結果">
    <h2>研究用：HU50BB抽象化モデル</h2>
    <p role="note">実ゲームGTO精度は未検証です。以下のEV・収束は抽象化モデル内の値であり、正式GTOの保証ではありません。</p>
    <p>HU・両者50BB・アンティ／レーキなし。サイズ：2.5／9／21／50BB。対象：{stages[stage]}。</p>
    <label>継続価値モデル<select aria-label="継続価値モデル" value={mode} onChange={event => setMode(event.target.value as typeof mode)}>
      <option value="flop_controller">フロップのベット／コール方策</option><option value="checkdown">チェックダウン比較モデル</option>
    </select></label>
    <p>フロップ方策は自分の手札と公開フロップから判断し、半ポットのベット1回まで。ターン・リバーはチェックで進めます。オールインはカード除去を反映したショーダウンで評価します。</p>
    <p>固定した標本利得表のNashConv：{model.abstract_nashconv_bb.toFixed(6)} BB（継続価値の期待値や実ゲームに対する利得上限ではありません）。169 / 169クラス。</p>
    {sensitivity && <p>独立seed間の行動頻度差：最大{(sensitivity.max_frequency_difference * 100).toFixed(1)}ポイント。到達確率で重み付けしたTV距離：{(sensitivity.reach_weighted_total_variation * 100).toFixed(1)}%。標本による戦略の不安定さが残っています。</p>}
    <div className="gto-legend">{context.actions.map((action, i) => <span key={action}><i style={{ background: colors[i % colors.length] }} />{names[action] ?? action}</span>)}</div>
    <div className="gto-matrix-scroll" tabIndex={0} role="region" aria-label="研究用169ハンド表">
      <table className="gto-matrix"><caption>抽象化モデルの試算・正式GTOではありません</caption>
        <tbody>{handGrid.map((row, i) => <tr key={i}>{row.map(label => <td key={label}>
          <button type="button" data-research-hand={label} aria-pressed={hand === label} aria-label={`研究用 ${label}`} style={{ background: bar(hands[label].frequencies) }} onClick={() => setHand(label)}><strong>{label}</strong><small>{hands[label].ev_bb.toFixed(3)} BB</small></button>
        </td>)}</tr>)}</tbody>
      </table>
    </div>
    <section aria-live="polite"><h3>{hand}：抽象化モデル内の頻度・EV</h3>
      <ul>{context.actions.map((action, i) => <li key={action}>{names[action] ?? action}：{(selected.frequencies[i] * 100).toFixed(1)}%／モデルEV {selected.action_ev_bb[i].toFixed(3)} BB</li>)}</ul>
      <p>モデルEV：{selected.ev_bb.toFixed(3)} BB。モデルの標本誤差を含む同時区間：[{selected.model_ev_interval_bb.map(x => x.toFixed(3)).join(', ')}] BB（99%）。実ゲームの近似誤差は含みません。</p>
    </section>
    <details><summary>検証条件と未検証範囲</summary>
      <p>各クラス対{abstractResearch.samples_per_class_pair}標本・{abstractResearch.iterations}反復・学習seed {abstractResearch.training_seed}。EVはブラインド支出を含む純損益です。</p>
      <p>固定方策の独立seed {model.heldout.seed}でのSB全体EV：{model.heldout.profile_sb_ev_bb.toFixed(4)} BB、区間[{model.heldout.interval_bb.map(x => x.toFixed(4)).join(', ')}] BB（{(model.heldout.confidence * 100).toFixed(1)}%）。各ハンドの区間とは集計範囲が異なります。</p>
      <p>信頼できる同条件の参照解との比較：未実施。実ゲームの近似誤差：未確定。省略サイズ・最適なポストフロップ戦略・正式20スタック条件は未検証です。</p>
      <p>方策：{model.policy_digest}／計算ソース：{abstractResearch.source_sha256}</p>
    </details>
  </section>
}
