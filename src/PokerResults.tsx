import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from './supabase'

type Tournament = { id: string; played_at: string; tournament_name: string; venue: string | null; rank: number | null; rank_unknown: boolean; entry_count: number | null; is_itm: boolean; total_entry_fee: number | null; prize_amount: number | null; is_public: boolean }
type Ring = { id: string; played_at: string; venue: string; game_type: string; big_blind: number; starting_stack: number; additional_stack: number; ending_stack: number; play_minutes: number; is_public: boolean }
type Cash = { id: string; played_at: string; venue: string; game_type: string; play_type: string; currency: string; profit_amount: number; profit_jpy: number; big_blind: number; play_minutes: number; is_public: boolean }
type Tab = 'tournament' | 'amusement' | 'cash'
const money = (n: number) => `${n < 0 ? '−' : ''}¥${Math.abs(Math.round(n)).toLocaleString('ja-JP')}`
const signed = (n: number, unit: string) => `${n > 0 ? '+' : ''}${Number(n.toFixed(1)).toLocaleString('ja-JP')}${unit}`
const cardStyle: React.CSSProperties = { padding: 16, background: '#121212', border: '1px solid #303030', borderRadius: 14 }

function PokerResults() {
  const navigate = useNavigate()
  const [tab, setTab] = useState<Tab>('tournament')
  const [tournaments, setTournaments] = useState<Tournament[]>([])
  const [rings, setRings] = useState<Ring[]>([])
  const [cash, setCash] = useState<Cash[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    async function load() {
      try {
        const { data: { user }, error: authError } = await supabase.auth.getUser()
        if (!active) return
        if (authError) throw authError
        if (!user) { navigate('/login'); return }
        const [t, r, c] = await Promise.all([
          supabase.from('poker_results').select('id, played_at, tournament_name, venue, rank, rank_unknown, entry_count, is_itm, total_entry_fee, prize_amount, is_public').eq('user_id', user.id).order('played_at', { ascending: false }),
          supabase.from('amusement_ring_results').select('id, played_at, venue, game_type, big_blind, starting_stack, additional_stack, ending_stack, play_minutes, is_public').eq('user_id', user.id).order('played_at', { ascending: false }),
          supabase.from('cash_game_results').select('id, played_at, venue, game_type, play_type, currency, profit_amount, profit_jpy, big_blind, play_minutes, is_public').eq('user_id', user.id).order('played_at', { ascending: false }),
        ])
        if (t.error || r.error || c.error) throw t.error || r.error || c.error
        if (!active) return
        setTournaments((t.data || []) as Tournament[])
        setRings((r.data || []) as Ring[])
        setCash((c.data || []) as Cash[])
      } catch (e) {
        if (active) setError(e instanceof Error ? e.message : '実績を読み込めませんでした。')
      } finally { if (active) setLoading(false) }
    }
    void load()
    return () => { active = false }
  }, [navigate])

  const tournamentStats = useMemo(() => {
    const knownFees = tournaments.filter(x => x.total_entry_fee != null)
    const fee = knownFees.reduce((s, x) => s + Number(x.total_entry_fee), 0)
    const prize = knownFees.reduce((s, x) => s + Number(x.prize_amount || 0), 0)
    const itm = tournaments.filter(x => x.is_itm).length
    return { fee, prize, itm, roi: fee > 0 ? (prize - fee) / fee * 100 : null, missingFees: knownFees.length !== tournaments.length }
  }, [tournaments])
  const ringStats = useMemo(() => rings.reduce((s, x) => {
    const bb = Number(x.big_blind)
    const result = bb > 0 ? (Number(x.ending_stack) - Number(x.starting_stack) - Number(x.additional_stack || 0)) / bb : 0
    return { bb: s.bb + result, minutes: s.minutes + Number(x.play_minutes || 0) }
  }, { bb: 0, minutes: 0 }), [rings])
  const cashStats = useMemo(() => cash.reduce((s, x) => ({ yen: s.yen + Number(x.profit_jpy || 0), minutes: s.minutes + Number(x.play_minutes || 0) }), { yen: 0, minutes: 0 }), [cash])
  const actions: Record<Tab, { create: string; label: string }> = {
    tournament: { create: '/profile/results/new', label: 'トーナメントを記録' },
    amusement: { create: '/profile/amusement-ring/new', label: 'リングを記録' },
    cash: { create: '/profile/cash-game/new', label: 'キャッシュを記録' },
  }
  const stats: { label: string; value: string }[] = tab === 'tournament' ? [
    { label: '参加回数', value: `${tournaments.length}回` },
    { label: 'ITM率', value: tournaments.length ? `${(tournamentStats.itm / tournaments.length * 100).toFixed(1)}%` : '—' },
    { label: '収支（参加費入力分）', value: money(tournamentStats.prize - tournamentStats.fee) },
    { label: 'ROI（参加費入力分）', value: tournamentStats.roi === null ? '—' : signed(tournamentStats.roi, '%') },
  ] : tab === 'amusement' ? [
    { label: '記録数', value: `${rings.length}回` },
    { label: '累計BB収支', value: signed(ringStats.bb, 'BB') },
    { label: 'プレイ時間', value: `${(ringStats.minutes / 60).toFixed(1)}時間` },
    { label: 'BB / 時間', value: ringStats.minutes ? signed(ringStats.bb / (ringStats.minutes / 60), 'BB') : '—' },
  ] : [
    { label: '記録数', value: `${cash.length}回` },
    { label: '円換算収支', value: money(cashStats.yen) },
    { label: 'プレイ時間', value: `${(cashStats.minutes / 60).toFixed(1)}時間` },
    { label: '円 / 時間', value: cashStats.minutes ? money(cashStats.yen / (cashStats.minutes / 60)) : '—' },
  ]

  return (
    <main className="app" style={{ paddingBottom: 90 }}>
      <div className="card" style={{ paddingTop: 18 }}>
        <button type="button" onClick={() => navigate('/tools')} style={{ width: 'auto', padding: 0, background: 'transparent', color: '#aaa', fontSize: 13 }}>← ポーカーツールに戻る</button>
        <h1 style={{ fontSize: 24, fontWeight: 900, margin: '20px 0 6px' }}>▥ 実戦記録</h1>
        <p style={{ fontSize: 12, color: '#999', lineHeight: 1.6, margin: '0 0 20px' }}>自分だけの実績管理。非公開の記録もここでは確認できます。</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 7, marginBottom: 20 }}>
          {([['tournament', 'トーナメント'], ['amusement', 'リング'], ['cash', 'キャッシュ']] as [Tab, string][]).map(([key, label]) => <button key={key} type="button" onClick={() => setTab(key)} style={{ minWidth: 0, padding: '12px 3px', borderRadius: 10, border: `1px solid ${tab === key ? '#fff' : '#303030'}`, background: tab === key ? '#fff' : '#181818', color: tab === key ? '#000' : '#bbb', fontSize: 12, fontWeight: 800 }}>{label}</button>)}
        </div>
        {loading ? <p style={{ color: '#aaa' }}>記録を読み込み中...</p> : error ? <p role="alert" style={{ color: '#ff9999' }}>読み込みエラー：{error}</p> : <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 9 }}>
            {stats.map(s => <div key={s.label} style={cardStyle}><div style={{ color: '#888', fontSize: 11 }}>{s.label}</div><div style={{ fontSize: 19, fontWeight: 900, marginTop: 8, overflowWrap: 'anywhere' }}>{s.value}</div></div>)}
          </div>
          {tab === 'tournament' && tournamentStats.missingFees && <p style={{ color: '#999', fontSize: 11, lineHeight: 1.6 }}>※ 参加費が未入力の記録は、収支・ROIの計算から除外しています。</p>}
          <button type="button" onClick={() => navigate(actions[tab].create)} style={{ width: '100%', marginTop: 19, padding: 14, borderRadius: 12, background: '#fff', color: '#000', fontSize: 14, fontWeight: 900 }}>＋ {actions[tab].label}</button>
          <h2 style={{ fontSize: 17, margin: '27px 0 12px' }}>記録一覧</h2>
          {tab === 'tournament' && (tournaments.length ? tournaments.map(x => <button key={x.id} type="button" onClick={() => navigate(`/profile/results/${x.id}/edit`)} style={{ ...cardStyle, display: 'block', width: '100%', color: '#fff', textAlign: 'left', marginBottom: 10 }}><div style={{ color: '#888', fontSize: 11 }}>{x.played_at}　{x.is_public ? '🌐 公開' : '🔒 非公開'}</div><div style={{ fontWeight: 800, fontSize: 16, marginTop: 7 }}>{x.tournament_name}</div><div style={{ color: '#aaa', fontSize: 12, marginTop: 6 }}>{x.venue || '会場未入力'}　/　{x.rank_unknown || x.rank == null ? '順位不明' : `${x.rank}位`}{x.entry_count ? ` / ${x.entry_count}人` : ''}{x.is_itm ? '　ITM' : ''}</div><div style={{ fontSize: 12, marginTop: 8 }}>獲得 {money(Number(x.prize_amount || 0))}　参加費 {x.total_entry_fee == null ? '未入力' : money(Number(x.total_entry_fee))}</div><div style={{ textAlign: 'right', color: '#aaa', fontSize: 11, marginTop: 9 }}>編集する ›</div></button>) : <p style={{ color: '#888', fontSize: 13 }}>まだトーナメント記録がありません。</p>)}
          {tab === 'amusement' && (rings.length ? rings.map(x => { const bb = Number(x.big_blind); const result = bb > 0 ? (Number(x.ending_stack) - Number(x.starting_stack) - Number(x.additional_stack || 0)) / bb : 0; return <button key={x.id} type="button" onClick={() => navigate(`/profile/amusement-ring/${x.id}/edit`)} style={{ ...cardStyle, width: '100%', color: '#fff', textAlign: 'left', marginBottom: 10 }}><div style={{ color: '#888', fontSize: 11 }}>{x.played_at}　{x.is_public ? '🌐 公開' : '🔒 非公開'}</div><div style={{ fontWeight: 800, fontSize: 16, marginTop: 7 }}>{x.venue}</div><div style={{ color: '#aaa', fontSize: 12, marginTop: 5 }}>{x.game_type}</div><div style={{ fontSize: 21, fontWeight: 900, marginTop: 8 }}>{signed(result, 'BB')}</div><div style={{ textAlign: 'right', color: '#aaa', fontSize: 11, marginTop: 9 }}>編集する ›</div></button> }) : <p style={{ color: '#888', fontSize: 13 }}>まだリング記録がありません。</p>)}
          {tab === 'cash' && (cash.length ? cash.map(x => <button key={x.id} type="button" onClick={() => navigate(`/profile/cash-game/${x.id}/edit`)} style={{ ...cardStyle, width: '100%', color: '#fff', textAlign: 'left', marginBottom: 10 }}><div style={{ color: '#888', fontSize: 11 }}>{x.played_at}　{x.is_public ? '🌐 公開' : '🔒 非公開'}</div><div style={{ fontWeight: 800, fontSize: 16, marginTop: 7 }}>{x.venue}</div><div style={{ color: '#aaa', fontSize: 12, marginTop: 5 }}>{x.game_type}　/　{x.play_type === 'online' ? 'オンライン' : 'ライブ'}</div><div style={{ fontSize: 21, fontWeight: 900, marginTop: 8 }}>{money(Number(x.profit_jpy || 0))}</div><div style={{ textAlign: 'right', color: '#aaa', fontSize: 11, marginTop: 9 }}>編集する ›</div></button>) : <p style={{ color: '#888', fontSize: 13 }}>まだキャッシュ記録がありません。</p>)}
        </>}
      </div>
    </main>
  )
}

export default PokerResults
