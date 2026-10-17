import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { supabase } from './supabase'

type ShareKind = 'cash' | 'amusement' | 'player-type'
type ShareData = { title: string; subtitle?: string; rows: { label: string; value: string }[] }

const numberText = (value: number | null | undefined, unit = '') =>
  value == null ? '' : `${Number(value).toLocaleString('ja-JP')}${unit}`
const formatDate = (value: string | null | undefined) => value ? value.replaceAll('-', '/') : ''

export default function PublicShare() {
  const { kind, id } = useParams<{ kind: ShareKind; id: string }>()
  const [status, setStatus] = useState<'loading' | 'ready' | 'missing' | 'error'>('loading')
  const [share, setShare] = useState<ShareData | null>(null)

  useEffect(() => {
    let active = true
    const load = async () => {
      setStatus('loading')
      setShare(null)
      if (!id || !/^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(id)) {
        setStatus('missing')
        return
      }
      if (kind === 'player-type') {
        // 公開用RPCで is_public=true を検証し、個別回答は公開しない。
        const { data, error } = await supabase.rpc('get_public_player_type_result', { p_user_id: id })
        if (!active) return
        if (error) { setStatus('error'); return }
        const record = (data || [])[0]
        if (!record) { setStatus('missing'); return }
        setShare({
          title: record.animal_name_ja || '動物タイプ診断',
          subtitle: record.catchphrase || 'Poker ID プレイヤータイプ診断',
          rows: [
            { label: '特徴', value: record.description || '' },
            { label: '強み', value: record.strength_text || '' },
            { label: '注意点', value: record.weakness_text || '' },
          ].filter(row => row.value),
        })
        setStatus('ready')
        return
      }
      if (kind === 'cash') {
        const { data, error } = await supabase.from('cash_game_results')
          .select('venue,played_at,game_type,small_blind,big_blind,currency,profit_amount,play_minutes')
          .eq('id', id).eq('is_public', true).maybeSingle()
        if (!active) return
        if (error) { setStatus('error'); return }
        if (!data) { setStatus('missing'); return }
        const currency = data.currency || ''
        setShare({
          title: 'キャッシュゲーム戦績',
          subtitle: data.venue || 'Poker IDで公開された戦績',
          rows: [
            { label: 'プレイ日', value: formatDate(data.played_at) },
            { label: 'ゲーム', value: data.game_type || '' },
            { label: 'ブラインド', value: data.small_blind != null && data.big_blind != null ? `${numberText(data.small_blind)} / ${numberText(data.big_blind)}` : '' },
            { label: '収支', value: data.profit_amount == null ? '' : `${numberText(data.profit_amount)} ${currency}` },
            { label: 'プレイ時間', value: data.play_minutes == null ? '' : `${numberText(data.play_minutes)}分` },
          ].filter(row => row.value),
        })
        setStatus('ready')
        return
      }
      if (kind === 'amusement') {
        const { data, error } = await supabase.from('amusement_ring_results')
          .select('venue,played_at,game_type,small_blind,big_blind,starting_stack,additional_stack,ending_stack,play_minutes')
          .eq('id', id).eq('is_public', true).maybeSingle()
        if (!active) return
        if (error) { setStatus('error'); return }
        if (!data) { setStatus('missing'); return }
        const net = data.ending_stack == null || data.starting_stack == null ? null
          : data.ending_stack - data.starting_stack - (data.additional_stack || 0)
        setShare({
          title: 'リングゲーム戦績',
          subtitle: data.venue || 'Poker IDで公開された戦績',
          rows: [
            { label: 'プレイ日', value: formatDate(data.played_at) },
            { label: 'ゲーム', value: data.game_type || '' },
            { label: 'ブラインド', value: data.small_blind != null && data.big_blind != null ? `${numberText(data.small_blind)} / ${numberText(data.big_blind)}` : '' },
            { label: 'スタック増減', value: net == null ? '' : numberText(net) },
            { label: 'プレイ時間', value: data.play_minutes == null ? '' : `${numberText(data.play_minutes)}分` },
          ].filter(row => row.value),
        })
        setStatus('ready')
        return
      }
      setStatus('missing')
    }
    void load().catch(() => { if (active) setStatus('error') })
    return () => { active = false }
  }, [kind, id])

  return (
    <main className="app" style={{ padding: '28px 14px', minHeight: '70vh' }}>
      <section className="card" style={{ maxWidth: 540, margin: '0 auto', padding: 22, color: '#f6f6f6' }}>
        <p style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>♠ Poker ID · 公開シェア</p>
        {status === 'loading' && <p role="status">記録を読み込んでいます...</p>}
        {status === 'error' && <p role="alert">記録の取得に失敗しました。時間をおいて再度お試しください。</p>}
        {status === 'missing' && <p role="status">この記録は非公開、削除済み、または存在しません。</p>}
        {status === 'ready' && share && <>
          <h1 style={{ fontSize: 25, marginBottom: 8, overflowWrap: 'anywhere' }}>{share.title}</h1>
          {share.subtitle && <p style={{ opacity: 0.8, overflowWrap: 'anywhere' }}>{share.subtitle}</p>}
          <dl style={{ display: 'grid', gap: 12, margin: '22px 0' }}>
            {share.rows.map(row => <div key={row.label} style={{ padding: '12px 14px', background: '#202020', borderRadius: 12 }}>
              <dt style={{ color: '#b8b8b8', fontSize: 12, marginBottom: 5 }}>{row.label}</dt>
              <dd style={{ margin: 0, fontSize: 16, overflowWrap: 'anywhere', whiteSpace: 'pre-wrap' }}>{row.value}</dd>
            </div>)}
          </dl>
        </>}
        <Link to="/timeline" style={{ display: 'inline-block', padding: '12px 16px', borderRadius: 10, background: '#f1f1f1', color: '#151515', fontWeight: 700, textDecoration: 'none', marginTop: 14 }}>Poker IDを見る →</Link>
      </section>
    </main>
  )
}
