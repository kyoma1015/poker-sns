import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { supabase } from './supabase'

type ShareKind = 'cash' | 'amusement' | 'player-type'

export default function PublicShare() {
  const { kind, id } = useParams<{ kind: ShareKind; id: string }>()
  const [state, setState] = useState<'loading' | 'ready' | 'missing'>('loading')
  const [title, setTitle] = useState('')
  const [details, setDetails] = useState<string[]>([])

  useEffect(() => {
    let active = true
    const load = async () => {
      setState('loading')
      setTitle('')
      setDetails([])
      if (!id || !/^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(id)) {
        setState('missing')
        return
      }
      if (kind === 'player-type') {
        // SECURITY DEFINER RPC applies is_public=true before returning a public diagnosis.
        const { data: result, error: rpcError } = await supabase.rpc('get_public_player_type_result', { p_user_id: id })
        if (!active) return
        const record = (result || [])[0]
        if (rpcError || !record) { setState('missing'); return }
        setTitle(record.animal_name_ja || '動物タイプ診断')
        setDetails([record.catchphrase, record.description].filter(Boolean))
        setState('ready')
        return
      }
      const table = kind === 'cash' ? 'cash_game_results' : kind === 'amusement' ? 'amusement_ring_results' : null
      if (!table) { setState('missing'); return }
      const { data, error } = await supabase.from(table)
        .select('venue,played_at').eq('id', id).eq('is_public', true).maybeSingle()
      if (!active) return
      if (error || !data) { setState('missing'); return }
      setTitle(kind === 'cash' ? 'キャッシュゲーム戦績' : 'リングゲーム戦績')
      setDetails([data.venue, data.played_at].filter(Boolean).map(String))
      setState('ready')
    }
    void load()
    return () => { active = false }
  }, [kind, id])

  return <main className="app"><div className="card">
    <h1>{state === 'ready' ? title : '共有された記録'}</h1>
    {state === 'loading' && <p>読み込み中...</p>}
    {state === 'missing' && <p>この記録は公開されていないか、存在しません。</p>}
    {state === 'ready' && details.map((item, index) => <p key={index}>{item}</p>)}
    <Link to="/timeline">Poker IDへ</Link>
  </div></main>
}
