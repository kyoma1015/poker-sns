import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { supabase } from './supabase'
import { getMyFollowedTags, normalizeTag, setTagFollow, SUGGESTED_TAGS } from './tagFollows'

export default function TagFollows() {
  const navigate = useNavigate()
  const [userId, setUserId] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [custom, setCustom] = useState('')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    void (async () => {
      const { data: { user } } = await supabase.auth.getUser()
      if (!active) return
      if (!user) { navigate('/login'); return }
      setUserId(user.id)
      try {
        const loaded = await getMyFollowedTags(user.id)
        if (active) setTags(loaded)
      } catch { if (active) setError('タグの取得に失敗しました。DBの準備状況を確認してください。') }
    })()
    return () => { active = false }
  }, [navigate])

  const toggle = async (tag: string) => {
    if (!userId || busy) return
    const following = !tags.includes(tag)
    setBusy(tag)
    setError('')
    try {
      await setTagFollow(userId, tag, following)
      setTags(previous => following ? [...previous, tag].sort() : previous.filter(item => item !== tag))
    } catch { setError('保存できませんでした。通信状況や権限を確認してください。') }
    finally { setBusy('') }
  }
  const candidates = [...new Set([...SUGGESTED_TAGS.map(normalizeTag), ...tags])]
  const customTag = normalizeTag(custom)
  return <main className="app" style={{ padding: 20, maxWidth: 680, margin: '0 auto' }}>
    <Link to="/timeline">← タイムライン</Link>
    <h1>フォロー中のタグ</h1>
    <p>興味のあるタグをフォローして、関連する投稿を探せます。</p>
    {error && <p role="alert">{error}</p>}
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
      {candidates.map(tag => <div key={tag} style={{ border: '1px solid #666', borderRadius: 12, padding: 12 }}>
        <Link to={`/timeline?tag=${encodeURIComponent(tag)}`}>#{tag}</Link>{' '}
        <button type="button" disabled={!userId || Boolean(busy)} onClick={() => void toggle(tag)}>
          {tags.includes(tag) ? 'フォロー解除' : 'フォロー'}
        </button>
      </div>)}
    </div>
    <form onSubmit={event => { event.preventDefault(); if (customTag && customTag.length <= 40 && !/\s/.test(customTag)) { void toggle(customTag); setCustom('') } }}>
      <label htmlFor="custom-tag">タグを追加</label>
      <input id="custom-tag" value={custom} maxLength={41} onChange={event => setCustom(event.target.value)} placeholder="#ポーカー" />
      <button type="submit" disabled={!userId || Boolean(busy) || !customTag || customTag.length > 40 || /\s/.test(customTag) || tags.includes(customTag)}>フォローする</button>
    </form>
    <h2>フォロー中（{tags.length}）</h2>
    {tags.length === 0 ? <p>まだフォローしているタグはありません。</p> :
      <ul>{tags.map(tag => <li key={tag}><Link to={`/timeline?tag=${encodeURIComponent(tag)}`}>#{tag} の投稿を見る</Link></li>)}</ul>}
  </main>
}
