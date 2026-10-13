import { useCallback, useEffect, useState, type CSSProperties } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from './supabase'

export type RegularAchievement = {
  id: string
  tournament_name: string
  played_at: string
  rank: number | null
  rank_unknown?: boolean
  entry_count: number | null
  venue?: string | null
  prize_amount?: number | null
  prize_description?: string | null
  is_featured: boolean
  is_public: boolean
}

type PastAchievement = {
  id: string
  tournament_name: string
  event_year: number
  event_month: number | null
  event_day: number | null
  rank: number
  entry_count: number | null
  venue: string | null
  prize_amount: number | null
  prize_description: string | null
  is_public: boolean
}
type CardData = {
  key: string
  source: 'regular' | 'past'
  id: string
  title: string
  when: string
  rank: number | null
  entryCount: number | null
  venue: string | null
  prizeAmount: number | null
  prizeDescription: string | null
  isPublic: boolean
}
const buttonStyle: CSSProperties = {
  width: 'auto', padding: '9px 13px', borderRadius: 10,
  background: '#1d1911', border: '1px solid #7d633b', color: '#f6d59a',
  fontSize: 12, fontWeight: 800, cursor: 'pointer',
}
function formatPastDate(row: PastAchievement) {
  return `${row.event_year}年${row.event_month == null ? '' : `${row.event_month}月`}${row.event_day == null ? '' : `${row.event_day}日`}`
}
function AchievementCard({ card, main, own, currentMain, onMain, busy }: {
  card: CardData; main: boolean; own: boolean; currentMain: boolean
  onMain: (card: CardData) => void; busy: boolean
}) {
  const navigate = useNavigate()
  const rankText = card.rank === 1 ? 'CHAMPION' : card.rank === 2 ? 'RUNNER-UP' : card.rank === 3 ? '3RD PLACE' : card.rank != null ? `RANK #${card.rank}` : 'TOURNAMENT RESULT'
  const tone = card.rank === 1 ? '#f2ca75' : card.rank === 2 ? '#cdd4df' : card.rank === 3 ? '#d8a77a' : '#e5cc9f'
  return (
    <article style={{
      padding: main ? '25px 17px' : '16px', borderRadius: main ? 21 : 16,
      background: main ? 'linear-gradient(145deg,#302314 0%,#181713 44%,#100f0e 100%)' : '#11100f',
      border: main ? '1px solid #b38b45' : '1px solid #4a3b27',
      boxShadow: main ? '0 8px 36px rgba(185,135,49,.13), inset 0 1px 0 rgba(255,218,142,.18)' : 'none',
      textAlign: main ? 'center' : 'left',
      overflow: 'hidden', position: 'relative',
    }}>
      {main && <div style={{ color: '#bba275', fontWeight: 800, fontSize: 10, letterSpacing: 3, marginBottom: 12 }}>✦ FEATURED ACHIEVEMENT ✦</div>}
      <div style={{ color: tone, fontWeight: 900, fontSize: main ? 28 : 17, letterSpacing: main ? 1.2 : 0.4, lineHeight: 1.4 }}>
        {card.rank != null && <span style={{ marginRight: 7 }}>{card.rank === 1 ? '🏆' : card.rank === 2 ? '🥈' : card.rank === 3 ? '🥉' : '✦'}</span>}
        {rankText}
      </div>
      <div style={{ color: '#f8f1e6', fontWeight: 850, fontSize: main ? 18 : 15, lineHeight: 1.6, marginTop: 8, overflowWrap: 'anywhere' }}>{card.title}</div>
      <div style={{ color: '#b5a990', fontSize: 12, marginTop: 7 }}>{card.when}{card.venue ? ` · ${card.venue}` : ''}</div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: main ? 'center' : 'flex-start', marginTop: 13 }}>
        {card.rank != null && <span style={{ color: '#ecd3a5', fontSize: 12, fontWeight: 800, padding: '5px 9px', border: '1px solid #675335', borderRadius: 8 }}>{card.rank}位</span>}
        {card.entryCount != null && <span style={{ color: '#c6b89e', fontSize: 12, padding: '5px 9px', border: '1px solid #433a30', borderRadius: 8 }}>参加 {card.entryCount}人</span>}
        {card.prizeAmount != null && card.prizeAmount > 0 && <span style={{ color: '#d3bb91', fontSize: 12, padding: '5px 9px', border: '1px solid #433a30', borderRadius: 8 }}>プライズ相当額 ¥{card.prizeAmount.toLocaleString()}</span>}
      </div>
      {!card.isPublic && <div style={{ color: '#d3aa91', fontSize: 12, marginTop: 12 }}>非公開：本人だけに表示しています</div>}
      {card.prizeDescription && <div style={{ color: '#aaa093', fontSize: 12, lineHeight: 1.6, marginTop: 11, overflowWrap: 'anywhere' }}>獲得内容：{card.prizeDescription}</div>}
      {own && <div style={{ display: 'flex', flexWrap: 'wrap', gap: 9, justifyContent: main ? 'center' : 'flex-start', marginTop: 15 }}>
        {!currentMain && card.isPublic && <button type="button" style={buttonStyle} disabled={busy} onClick={() => onMain(card)}>☆ メイン実績に設定</button>}
        {currentMain && <span style={{ color: '#f1ce85', fontSize: 12, fontWeight: 700, padding: 10 }}>★ メイン実績</span>}
        <button type="button" style={{ ...buttonStyle, color: '#ddd', background: '#1a1a1a', borderColor: '#3b3b3b' }} onClick={() => navigate(card.source === 'past' ? `/profile/achievements/${card.id}/edit` : `/profile/results/${card.id}/edit`)}>編集する →</button>
      </div>}
    </article>
  )
}
export default function TournamentAchievementShowcase({ profileId, own, regularResults }: {
  profileId: string
  own: boolean
  regularResults: RegularAchievement[]
}) {
  const navigate = useNavigate()
  const [past, setPast] = useState<PastAchievement[]>([])
  const [highlight, setHighlight] = useState<{ source_type: string; source_id: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const refresh = useCallback(async () => {
    const [pastResult, highlightResult] = await Promise.all([
      supabase.from('poker_past_achievements').select('id, tournament_name, event_year, event_month, event_day, rank, entry_count, venue, prize_amount, prize_description, is_public').eq('user_id', profileId).order('event_year', { ascending: false }).order('created_at', { ascending: false }),
      supabase.from('poker_achievement_highlights').select('source_type, source_id').eq('user_id', profileId).maybeSingle(),
    ])
    if (pastResult.error || highlightResult.error) {
      setError('大会実績の読み込みに失敗しました。画面を更新してください。')
      console.error(pastResult.error || highlightResult.error)
      return
    }
    setPast((pastResult.data || []) as PastAchievement[])
    setHighlight(highlightResult.data ?? null)
    setError('')
  }, [profileId])
  useEffect(() => { void refresh() }, [refresh])
  const cards: CardData[] = [
    ...past.filter(row => own || row.is_public).map(row => ({ key: `past:${row.id}`, source: 'past' as const, id: row.id, title: row.tournament_name, when: formatPastDate(row), rank: row.rank, entryCount: row.entry_count, venue: row.venue, prizeAmount: row.prize_amount == null ? null : Number(row.prize_amount), prizeDescription: row.prize_description, isPublic: row.is_public })),
    ...regularResults.filter(row => row.is_featured && row.is_public).map(row => ({ key: `regular:${row.id}`, source: 'regular' as const, id: row.id, title: row.tournament_name, when: row.played_at ? new Date(`${row.played_at}T00:00:00`).toLocaleDateString('ja-JP') : '', rank: row.rank_unknown ? null : row.rank, entryCount: row.entry_count, venue: row.venue ?? null, prizeAmount: row.prize_amount ?? null, prizeDescription: row.prize_description ?? null, isPublic: true })),
  ]
  const publicCards = cards.filter(card => card.isPublic)
  const selected = publicCards.find(card => highlight?.source_type === card.source && highlight.source_id === String(card.id)) ?? publicCards[0]
  const others = cards.filter(card => card.key !== selected?.key)
  const chooseMain = async (card: CardData) => {
    if (busy || !own) return
    setBusy(true); setError('')
    const { error: saveError } = await supabase.from('poker_achievement_highlights').upsert({ user_id: profileId, source_type: card.source, source_id: String(card.id), updated_at: new Date().toISOString() }, { onConflict: 'user_id' })
    if (saveError) setError(`メイン実績の設定に失敗しました：${saveError.message}`)
    else setHighlight({ source_type: card.source, source_id: String(card.id) })
    setBusy(false)
  }
  if (!own && cards.length === 0) return null
  return (
    <section style={{ padding: '22px 0', borderBottom: '1px solid #302719' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
        <div>
          <div style={{ color: '#f4d59e', fontSize: 18, fontWeight: 900, letterSpacing: .3 }}>🏆 主なトーナメント実績</div>
          <div style={{ color: '#9b8a70', fontSize: 11, marginTop: 5 }}>TOURNAMENT ACHIEVEMENTS</div>
        </div>
        {own && <button type="button" style={{ ...buttonStyle, whiteSpace: 'nowrap' }} onClick={() => navigate('/profile/achievements/new')}>＋ 実績を追加</button>}
      </div>
      {error && <div role="alert" style={{ marginTop: 12, color: '#ffc0af', fontSize: 12 }}>{error}</div>}
      {selected ? <div style={{ marginTop: 17 }}><AchievementCard card={selected} main own={own} currentMain onMain={chooseMain} busy={busy} /></div> : <div style={{ border: '1px dashed #665136', background: '#17140f', borderRadius: 16, padding: 20, textAlign: 'center', marginTop: 16 }}>
        <div style={{ fontSize: 24, marginBottom: 8 }}>🏆</div>
        <div style={{ color: '#dac396', fontSize: 13 }}>過去の大会での活躍をプロフィールに飾ろう</div>
      </div>}
      {others.length > 0 && <div style={{ display: 'grid', gap: 10, marginTop: 12 }}>{others.map(card => <AchievementCard key={card.key} card={card} main={false} own={own} currentMain={false} onMain={chooseMain} busy={busy} />)}</div>}
      {own && <p style={{ marginTop: 12, color: '#827b71', fontSize: 11, lineHeight: 1.6 }}>過去の実績は通常の戦績分析・収支・ROI・ITM率・大会数に反映されません。既存のトーナメント記録から指定した「主な実績」もここに表示されます。</p>}
    </section>
  )
}
