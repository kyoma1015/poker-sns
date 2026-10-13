import { useEffect, useState, type CSSProperties, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { supabase } from './supabase'

const field: CSSProperties = { width: '100%', boxSizing: 'border-box', background: '#181818', color: '#f4f4f4', border: '1px solid #393939', borderRadius: 11, padding: '13px 12px', fontSize: 15 }
const labelStyle: CSSProperties = { display: 'grid', gap: 7, marginBottom: 18, fontSize: 13, color: '#ddd', fontWeight: 750 }
const button: CSSProperties = { width: '100%', padding: 14, background: '#d6ad60', borderRadius: 12, color: '#17120b', fontSize: 15, fontWeight: 850, border: 'none' }
const isDigits = (value: string) => /^\d+$/.test(value)
const optionalInteger = (value: string) => value.trim() === '' ? null : Number(value)

export default function PastTournamentAchievementForm() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const editing = !!id
  const [userId, setUserId] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [name, setName] = useState('')
  const [year, setYear] = useState('')
  const [month, setMonth] = useState('')
  const [day, setDay] = useState('')
  const [rank, setRank] = useState('')
  const [entries, setEntries] = useState('')
  const [venue, setVenue] = useState('')
  const [entryFee, setEntryFee] = useState('')
  const [prize, setPrize] = useState('')
  const [prizeDetail, setPrizeDetail] = useState('')
  const [memo, setMemo] = useState('')
  const [isPublic, setIsPublic] = useState(true)
  useEffect(() => {
    let cancelled = false
    const load = async () => {
      const { data: { user }, error: userError } = await supabase.auth.getUser()
      if (cancelled) return
      if (userError || !user) { navigate('/login'); return }
      setUserId(user.id)
      if (id) {
        const { data, error: loadError } = await supabase.from('poker_past_achievements').select('*').eq('id', id).eq('user_id', user.id).maybeSingle()
        if (cancelled) return
        if (loadError || !data) { setError('実績を取得できません。'); setLoading(false); return }
        setName(data.tournament_name ?? '')
        setYear(String(data.event_year))
        setMonth(data.event_month == null ? '' : String(data.event_month))
        setDay(data.event_day == null ? '' : String(data.event_day))
        setRank(String(data.rank))
        setEntries(data.entry_count == null ? '' : String(data.entry_count))
        setVenue(data.venue ?? '')
        setEntryFee(data.entry_fee == null ? '' : String(data.entry_fee))
        setPrize(data.prize_amount == null ? '' : String(data.prize_amount))
        setPrizeDetail(data.prize_description ?? '')
        setMemo(data.memo ?? '')
        setIsPublic(!!data.is_public)
      }
      setLoading(false)
    }
    void load()
    return () => { cancelled = true }
  }, [id, navigate])

  const save = async (e: FormEvent) => {
    e.preventDefault()
    if (!userId || saving) return
    const title = name.trim()
    const y = Number(year), m = optionalInteger(month), d = optionalInteger(day)
    const r = Number(rank), count = optionalInteger(entries)
    if (!title || title.length > 160 || !isDigits(year) || y < 1900 || y > new Date().getFullYear() + 1) { setError('大会名と開催年を確認してください。'); return }
    if ((month && (!isDigits(month) || m == null || m < 1 || m > 12)) || (day && (!month || !isDigits(day) || d == null || d < 1 || d > 31))) { setError('月日を確認してください。日だけの指定はできません。'); return }
    if (m != null && d != null && new Date(y, m - 1, d).getMonth() !== m - 1) { setError('存在しない日付です。'); return }
    if (!isDigits(rank) || r < 1 || (count != null && (!isDigits(entries) || count < r))) { setError('順位と参加人数を確認してください。参加人数は順位以上にしてください。'); return }
    if ([entryFee, prize].some(value => value.trim() !== '' && (!isDigits(value) || Number(value) > 99999999999999))) { setError('金額は0以上の整数で入力してください。'); return }
    if (venue.length > 160 || prizeDetail.length > 300 || memo.length > 1000) { setError('文字数の上限を超えています。'); return }
    setSaving(true); setError('')
    if (!editing) {
      const { data: duplicates, error: duplicateError } = await supabase.from('poker_past_achievements').select('id').eq('user_id', userId).eq('event_year', y).eq('tournament_name', title).limit(1)
      if (duplicateError) { setError(`重複確認に失敗しました：${duplicateError.message}`); setSaving(false); return }
      if ((duplicates?.length ?? 0) > 0 && !window.confirm('同じ年・大会名の実績が既にあります。重複して登録しますか？')) { setSaving(false); return }
    }
    const payload = {
      tournament_name: title, event_year: y, event_month: m, event_day: d,
      rank: r, entry_count: count, venue: venue.trim() || null,
      entry_fee: optionalInteger(entryFee), prize_amount: optionalInteger(prize),
      prize_description: prizeDetail.trim() || null, memo: memo.trim() || null,
      is_public: isPublic, updated_at: new Date().toISOString(),
    }
    const result = editing
      ? await supabase.from('poker_past_achievements').update(payload).eq('id', id).eq('user_id', userId).select('id').single()
      : await supabase.from('poker_past_achievements').insert({ ...payload, user_id: userId }).select('id').single()
    setSaving(false)
    if (result.error) { setError(`保存に失敗しました：${result.error.message}`); return }
    navigate('/profile', { replace: true })
  }
  const remove = async () => {
    if (!id || !userId || saving) return
    if (!window.confirm('この過去の大会実績を削除しますか？削除後は元に戻せません。')) return
    setSaving(true); setError('')
    const { error: deleteError } = await supabase.from('poker_past_achievements').delete().eq('id', id).eq('user_id', userId)
    setSaving(false)
    if (deleteError) { setError(`削除に失敗しました：${deleteError.message}`); return }
    navigate('/profile', { replace: true })
  }
  return <main className="app"><div className="card" style={{ maxWidth: 650, margin: 'auto', padding: '22px 20px 80px' }}>
    <button type="button" onClick={() => navigate('/profile')} style={{ background: 'transparent', color: '#aaa', width: 'auto', padding: 5, marginBottom: 15 }}>‹ プロフィールへ戻る</button>
    <h1 style={{ fontSize: 23, margin: '0 0 8px' }}>{editing ? '過去の大会実績を編集' : '過去の大会実績を追加'}</h1>
    <div style={{ background: '#292014', border: '1px solid #9d7738', color: '#edd2a0', padding: 15, borderRadius: 12, fontSize: 12, lineHeight: 1.8, marginBottom: 24 }}>
      <strong>重要：過去の大会実績専用の登録です。</strong>ここで登録した実績は収支・ROI・ITM率・大会数・ランキング・グラフに一切反映されません。通常の戦績記録を開始した後の大会は、<button type="button" onClick={() => navigate('/profile/results/new')} style={{ border: 'none', padding: 0, width: 'auto', background: 'transparent', color: '#f6d388', textDecoration: 'underline', fontWeight: 800 }}>通常のトーナメント記録</button>から登録してください。
    </div>
    {loading ? <div>読み込み中...</div> : <form onSubmit={save}>
      <label style={labelStyle}>大会名（必須）<input style={field} value={name} maxLength={160} onChange={e => setName(e.target.value)} required placeholder="例：〇〇 POKER OPEN" /></label>
      <label style={labelStyle}>開催年（必須）<input style={field} inputMode="numeric" type="number" min="1900" max="2100" value={year} onChange={e => setYear(e.target.value)} required placeholder="2025" /></label>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <label style={labelStyle}>開催月（任意）<input style={field} inputMode="numeric" type="number" min="1" max="12" value={month} onChange={e => {setMonth(e.target.value);if(!e.target.value)setDay('')}} placeholder="月" /></label>
        <label style={labelStyle}>開催日（任意）<input style={field} inputMode="numeric" type="number" min="1" max="31" value={day} onChange={e => setDay(e.target.value)} disabled={!month} placeholder="日" /></label>
      </div>
      <label style={labelStyle}>順位（必須）<input style={field} inputMode="numeric" type="number" min="1" value={rank} onChange={e => setRank(e.target.value)} required placeholder="例：1" /></label>
      <label style={labelStyle}>参加人数（任意）<input style={field} inputMode="numeric" type="number" min="1" value={entries} onChange={e => setEntries(e.target.value)} placeholder="例：320" /></label>
      <label style={labelStyle}>開催会場（任意）<input style={field} value={venue} maxLength={160} onChange={e => setVenue(e.target.value)} placeholder="店舗・会場名" /></label>
      <label style={labelStyle}>バイイン（任意・円）<input style={field} inputMode="numeric" type="number" min="0" value={entryFee} onChange={e => setEntryFee(e.target.value)} placeholder="例：10000" /></label>
      <label style={labelStyle}>獲得賞金・プライズ相当額（任意・円）<input style={field} inputMode="numeric" type="number" min="0" value={prize} onChange={e => setPrize(e.target.value)} placeholder="例：50000" /></label>
      <label style={labelStyle}>獲得内容（任意）<textarea style={{ ...field, resize: 'vertical' }} rows={2} maxLength={300} value={prizeDetail} onChange={e => setPrizeDetail(e.target.value)} placeholder="例：トロフィー・記念品" /></label>
      <label style={labelStyle}>メモ（任意）<textarea style={{ ...field, resize: 'vertical' }} rows={3} maxLength={1000} value={memo} onChange={e => setMemo(e.target.value)} /></label>
      <label style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24, fontSize: 13, color: '#ddd' }}><input type="checkbox" checked={isPublic} onChange={e => setIsPublic(e.target.checked)} style={{ width: 21, height: 21 }} />この実績をプロフィールに公開する</label>
      {error && <p role="alert" style={{ color: '#ffb9a8', fontSize: 13 }}>{error}</p>}
      <button type="submit" style={button} disabled={saving}>{saving ? '保存中...' : editing ? '変更を保存する' : '実績を登録する'}</button>
      {editing && <button type="button" onClick={() => void remove()} disabled={saving} style={{ ...button, background: 'transparent', color: '#ff9999', border: '1px solid #793c3c', marginTop: 18 }}>この実績を削除する</button>}
    </form>}
  </div></main>
}
