import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from './supabase'

type Person = { id: string; display_name: string | null; poker_id: string | null; avatar_url: string | null }
type Section = 'blocks' | 'mutes'

export default function Settings() {
  const navigate = useNavigate()
  const [section, setSection] = useState<Section>('blocks')
  const [blocks, setBlocks] = useState<Person[]>([])
  const [mutes, setMutes] = useState<Person[]>([])
  const [userId, setUserId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busyId, setBusyId] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) { navigate('/login'); return }
    setUserId(user.id)
    const [blockResult, muteResult] = await Promise.all([
      supabase.from('user_blocks').select('blocked_id').eq('blocker_id', user.id),
      supabase.from('user_mutes').select('muted_id').eq('muter_id', user.id),
    ])
    if (blockResult.error || muteResult.error) {
      console.error('設定一覧取得エラー', blockResult.error, muteResult.error)
      setError('一覧を取得できませんでした。データベースのアクセス権限を確認してください。')
      setLoading(false)
      return
    }
    const blockedIds = (blockResult.data || []).map(row => row.blocked_id as string)
    const mutedIds = (muteResult.data || []).map(row => row.muted_id as string)
    const ids = [...new Set([...blockedIds, ...mutedIds])]
    if (ids.length === 0) { setBlocks([]); setMutes([]); setLoading(false); return }
    const { data: profiles, error: profileError } = await supabase.from('profiles')
      .select('id, display_name, poker_id, avatar_url').in('id', ids)
    if (profileError) {
      console.error('プロフィール取得エラー', profileError)
      setError('ユーザー情報を取得できませんでした。')
      setLoading(false)
      return
    }
    const byId = new Map((profiles || []).map(person => [person.id, person as Person]))
    const personFor = (id: string): Person => byId.get(id) || { id, display_name: 'ユーザー', poker_id: null, avatar_url: null }
    setBlocks(blockedIds.map(personFor))
    setMutes(mutedIds.map(personFor))
    setLoading(false)
  }, [navigate])

  useEffect(() => { void load() }, [load])

  const remove = async (person: Person) => {
    if (!userId || busyId) return
    const isBlock = section === 'blocks'
    if (!window.confirm(`${person.display_name || 'このユーザー'}の${isBlock ? 'ブロック' : 'ミュート'}を解除しますか？`)) return
    setBusyId(person.id)
    setError('')
    const { error: deleteError } = isBlock
      ? await supabase.from('user_blocks').delete().eq('blocker_id', userId).eq('blocked_id', person.id)
      : await supabase.from('user_mutes').delete().eq('muter_id', userId).eq('muted_id', person.id)
    if (deleteError) { console.error(deleteError); setError('解除できませんでした。もう一度お試しください。') }
    else if (isBlock) setBlocks(prev => prev.filter(row => row.id !== person.id))
    else setMutes(prev => prev.filter(row => row.id !== person.id))
    setBusyId(null)
  }

  const people = section === 'blocks' ? blocks : mutes
  return (
    <main className="app">
      <div className="card" style={{ paddingTop: 0, minHeight: '70vh' }}>
        <header style={{ position: 'sticky', top: 0, zIndex: 20, margin: '0 -20px', padding: '15px 20px', display: 'flex', alignItems: 'center', gap: 14, background: 'rgba(0,0,0,.92)', borderBottom: '1px solid #242424' }}>
          <button type="button" onClick={() => navigate('/profile')} style={{ width: 'auto', background: 'transparent', padding: '6px 2px', color: '#fff', fontSize: 20 }}>‹</button>
          <div style={{ fontSize: 19, fontWeight: 800 }}>設定</div>
        </header>
        <div style={{ marginTop: 24, fontSize: 16, fontWeight: 800 }}>ユーザー管理</div>
        <div style={{ marginTop: 6, fontSize: 12, color: '#888' }}>ブロック・ミュートしているプレイヤーを管理できます。</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 20 }}>
          {([['blocks', 'ブロック中', blocks.length], ['mutes', 'ミュート中', mutes.length]] as const).map(([key, label, count]) => (
            <button type="button" key={key} onClick={() => setSection(key)} style={{ padding: '12px 8px', borderRadius: 12, border: section === key ? '1px solid #fff' : '1px solid #333', background: section === key ? '#252525' : '#111', color: '#fff', fontWeight: 700, fontSize: 13 }}>{label} ({count})</button>
          ))}
        </div>
        {error && <div role="alert" style={{ color: '#ff9d9d', marginTop: 18, fontSize: 13 }}>{error} <button type="button" onClick={() => void load()} style={{ width: 'auto', marginLeft: 8, padding: '6px 10px' }}>再読み込み</button></div>}
        {loading ? <div style={{ color: '#888', padding: '38px 0', textAlign: 'center' }}>読み込み中...</div> : !error && people.length === 0 ? <div style={{ color: '#888', padding: '38px 0', textAlign: 'center', fontSize: 13 }}>{section === 'blocks' ? 'ブロック中' : 'ミュート中'}のユーザーはいません</div> : (
          <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
            {people.map(person => (
              <div key={person.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: 12, borderRadius: 14, border: '1px solid #292929', background: '#101010' }}>
                <button type="button" onClick={() => navigate(`/player/${person.id}`)} style={{ width: 'auto', minWidth: 0, flex: 1, display: 'flex', alignItems: 'center', gap: 10, background: 'transparent', padding: 0, textAlign: 'left', color: '#fff' }}>
                  {person.avatar_url ? <img src={person.avatar_url} alt="" style={{ width: 42, height: 42, borderRadius: '50%', objectFit: 'cover' }} /> : <span style={{ width: 42, height: 42, borderRadius: '50%', display: 'grid', placeItems: 'center', background: '#222' }}>♠</span>}
                  <span style={{ minWidth: 0 }}><span style={{ display: 'block', fontWeight: 700, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{person.display_name || 'ユーザー'}</span><span style={{ display: 'block', fontSize: 11, color: '#888', marginTop: 3 }}>@{person.poker_id || '—'}</span></span>
                </button>
                <button type="button" disabled={busyId !== null} onClick={() => void remove(person)} style={{ width: 'auto', flexShrink: 0, padding: '9px 12px', background: 'transparent', color: '#fff', border: '1px solid #555', borderRadius: 999, fontSize: 12 }}>{busyId === person.id ? '処理中...' : '解除'}</button>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
