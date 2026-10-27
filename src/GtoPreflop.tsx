import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { canonicalQuery, findVerifiedRange, handGrid, positions } from './gto/rangeCatalog'
import type { RangeQuery, ReviewedCertificate, VerifiedRange } from './gto/rangeCatalog'
import { reviewedCertificates, verifiedCatalog } from './gto/verifiedCatalog'
import './GtoPreflop.css'

const stages = { rfi: 'RFI（自分まで全員フォールド）', vs_open: 'オープンへの対応',
  vs_3bet: '3ベットへの対応', vs_4bet: '4ベットへの対応' }
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
  function change(patch: Partial<RangeQuery>) {
    setForm(previous => ({ ...previous, ...patch }))
    setResult(null); setError(''); setMessage('条件を入力して検索してください。')
  }
  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      const query = canonicalQuery(form)
      const match = findVerifiedRange(query, catalog, certificates)
      setResult(match); setSelected('AA'); setError('')
      setMessage(match ? '計算条件と検証根拠が一致するデータを表示しています。' : 'この条件の検証済みデータはまだありません。')
    } catch (caught) {
      setResult(null); setError(caught instanceof Error ? caught.message : '検索条件を確認してください。')
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
        <form aria-label="プリフロップ検索条件" onSubmit={search}>
          <fieldset className="gto-fields"><legend>計算条件</legend>
            <label>ゲーム形式<select aria-label="ゲーム形式" value={form.format} onChange={event => change({ format: event.target.value as RangeQuery['format'], rakePct: '0', rakeCapBb: null })}>
              <option value="mtt">MTT（chipEV）</option><option value="ring">リングゲーム</option>
            </select></label>
            <label>人数<select aria-label="人数" value={form.players} onChange={event => {
              const players = Number(event.target.value); change({ players, seat: positions(players)[0].seat })
            }}>{Array.from({ length: 8 }, (_, i) => i + 2).map(n => <option key={n} value={n}>{n}人</option>)}</select></label>
            <label>ポジション<select aria-label="ポジション" value={form.seat} onChange={event => change({ seat: Number(event.target.value) })}>
              {positions(form.players).map(position => <option key={position.seat} value={position.seat}>{position.label}</option>)}
            </select></label>
            <label>有効スタック（BB）<input aria-label="有効スタック（BB）" required inputMode="decimal" value={form.stackBb} placeholder="例：100" onChange={event => change({ stackBb: event.target.value })} /></label>
            <label>BBアンティ<select aria-label="BBアンティ" value={form.anteBb} onChange={event => change({ anteBb: event.target.value as RangeQuery['anteBb'] })}>
              <option value="0">なし</option><option value="1">1 BB</option>
            </select></label>
            <label>レーキ<select aria-label="レーキ" disabled={form.format === 'mtt'} value={form.rakePct} onChange={event => change({ rakePct: event.target.value as RangeQuery['rakePct'] })}>
              <option value="0">0%</option><option value="5">5%</option><option value="10">10%</option>
            </select></label>
            <label>レーキ上限<select aria-label="レーキ上限" disabled={form.format === 'mtt'} value={form.rakeCapBb ?? 'none'} onChange={event => change({ rakeCapBb: event.target.value === 'none' ? null : event.target.value as '5' | '10' })}>
              <option value="none">上限なし</option><option value="5">5 BB</option><option value="10">10 BB</option>
            </select></label>
            <label>オープンサイズ（BB）<input aria-label="オープンサイズ（BB）" required inputMode="decimal" value={form.openBb} placeholder="合計額" onChange={event => change({ openBb: event.target.value })} /></label>
            <label>3ベットサイズ（BB）<input aria-label="3ベットサイズ（BB）" required inputMode="decimal" value={form.threeBetBb} placeholder="合計額" onChange={event => change({ threeBetBb: event.target.value })} /></label>
            <label>4ベットサイズ（BB）<input aria-label="4ベットサイズ（BB）" required inputMode="decimal" value={form.fourBetBb} placeholder="合計額" onChange={event => change({ fourBetBb: event.target.value })} /></label>
            <label className="gto-wide">対象局面<select aria-label="対象局面" value={form.stage} onChange={event => change({ stage: event.target.value as RangeQuery['stage'] })}>
              {Object.entries(stages).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
            </select></label>
          </fieldset>
          <button className="gto-search" type="submit">検証済みレンジを検索</button>
        </form>
        {error && <p role="alert" className="gto-error">{error}</p>}
        <p role="status" className="gto-status">{message}</p>
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
          <p>EV：{selectedRow.evBb.toFixed(3)} BB</p>
          <p>Coverage：169 / 169ハンド・1326 / 1326コンビネーション</p>
          <details><summary>計算条件と収束の検証根拠</summary>
            <p>対象ゲーム全体の一方的な戦略変更による利得上限：{result.certificate.upperBoundBb} BB</p>
            <p>検証時の許容値：{result.certificate.acceptedToleranceBb} BB</p>
            <p>根拠：{result.certificate.reviewReference}</p>
            <p>ポリシー：{result.policyDigest}</p><p>計算条件：{result.configDigest}</p>
            <p>研究用の局所指標やEVサンプリング誤差を、ゲーム全体の収束根拠として使用していません。</p>
          </details>
        </section>}
      </section>
    </main>
  )
}
