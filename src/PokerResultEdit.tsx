import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { supabase } from './supabase'

function PokerResultEdit() {
  const navigate = useNavigate()
  const { id } = useParams()

  const [tournamentName, setTournamentName] = useState('')
  const [playedAt, setPlayedAt] = useState('')
  const [venue, setVenue] = useState('')
  const [rank, setRank] = useState('')
  const [rankUnknown, setRankUnknown] = useState(false)
  const [entryCount, setEntryCount] = useState('')
  const [isItm, setIsItm] = useState(false)
  const [entryFee, setEntryFee] = useState('')
  const [bullets, setBullets] = useState('1')
  const [totalEntryFee, setTotalEntryFee] = useState('')
  const [totalFeeEdited, setTotalFeeEdited] = useState(false)
  const [prizeAmount, setPrizeAmount] = useState('0')
  const [entryTiming, setEntryTiming] = useState<'early' | 'middle' | 'late'>('early')
  const [showDetails, setShowDetails] = useState(false)
  const [entryBb, setEntryBb] = useState('')
  const [gameType, setGameType] = useState('')
  const [prizeDescription, setPrizeDescription] = useState('')
  const [memo, setMemo] = useState('')
  const [isPublic, setIsPublic] = useState(false)
  const [isFeatured, setIsFeatured] = useState(false)
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    const loadResult = async () => {
      if (!id) return navigate('/profile')
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return navigate('/login')

      const { data, error } = await supabase
        .from('poker_results')
        .select('id, user_id, tournament_name, played_at, venue, rank, rank_unknown, entry_count, is_itm, entry_fee, bullets, total_entry_fee, prize_amount, entry_timing, entry_bb, game_type, prize_description, memo, is_public, is_featured')
        .eq('id', id)
        .eq('user_id', user.id)
        .maybeSingle()

      if (error) {
        console.error(error)
        setMessage(`読み込みに失敗しました：${error.message}`)
        setIsLoading(false)
        return
      }
      if (!data) {
        setMessage('このトーナメント記録は存在しないか、編集する権限がありません。')
        setIsLoading(false)
        return
      }

      setTournamentName(data.tournament_name || '')
      setPlayedAt(data.played_at || '')
      setVenue(data.venue || '')
      setRank(data.rank == null ? '' : String(data.rank))
      setRankUnknown(data.rank_unknown === true)
      setEntryCount(data.entry_count == null ? '' : String(data.entry_count))
      setIsItm(data.is_itm === true)
      setEntryFee(data.entry_fee == null ? '' : String(data.entry_fee))
      setBullets(data.bullets == null ? '1' : String(data.bullets))
      setTotalEntryFee(data.total_entry_fee == null ? '' : String(data.total_entry_fee))
      setTotalFeeEdited(data.total_entry_fee != null)
      setPrizeAmount(data.prize_amount == null ? '0' : String(data.prize_amount))
      setEntryTiming(data.entry_timing === 'middle' || data.entry_timing === 'late' ? data.entry_timing : 'early')
      setEntryBb(data.entry_bb == null ? '' : String(data.entry_bb))
      setGameType(data.game_type || '')
      setPrizeDescription(data.prize_description || '')
      setMemo(data.memo || '')
      setIsPublic(data.is_public === true)
      setIsFeatured(data.is_featured === true)
      if (data.entry_bb != null || data.game_type || data.prize_description) setShowDetails(true)
      setIsLoading(false)
    }
    loadResult()
  }, [id, navigate])

  const calculatedTotalFee = () => {
    if (entryFee === '' || bullets === '') return ''
    const fee = Number(entryFee)
    const count = Number(bullets)
    if (!Number.isFinite(fee) || !Number.isFinite(count)) return ''
    return String(fee * count)
  }

  const displayedTotalFee = totalFeeEdited ? totalEntryFee : calculatedTotalFee()
  const formatYen = (value: string) => value === '' || !Number.isFinite(Number(value)) ? '—' : `${Number(value).toLocaleString('ja-JP')}円`

  const handlePublicChange = (value: boolean) => {
    setIsPublic(value)
    if (!value) setIsFeatured(false)
  }

  const handleSave = async () => {
    if (!id) return
    setMessage('')
    const name = tournamentName.trim()
    if (!name) return setMessage('トーナメント名を入力してください。')
    if (!playedAt) return setMessage('開催日を入力してください。')
    if (!rankUnknown && rank === '') return setMessage('順位を入力するか「順位不明」を選択してください。')

    const rankNumber = rankUnknown || rank === '' ? null : Number(rank)
    const entryCountNumber = entryCount === '' ? null : Number(entryCount)
    const entryFeeNumber = entryFee === '' ? null : Number(entryFee)
    const bulletsNumber = Number(bullets)
    const totalNumber = displayedTotalFee === '' ? null : Number(displayedTotalFee)
    const prizeNumber = prizeAmount === '' ? 0 : Number(prizeAmount)
    const bbNumber = entryBb === '' ? null : Number(entryBb)

    if (rankNumber !== null && (!Number.isInteger(rankNumber) || rankNumber < 1)) return setMessage('順位は1以上の整数で入力してください。')
    if (entryCountNumber !== null && (!Number.isInteger(entryCountNumber) || entryCountNumber < 1)) return setMessage('参加人数は1以上の整数で入力してください。')
    if (rankNumber !== null && entryCountNumber !== null && rankNumber > entryCountNumber) return setMessage('順位が参加人数を超えています。')
    if (entryFeeNumber !== null && (!Number.isFinite(entryFeeNumber) || entryFeeNumber < 0)) return setMessage('参加費は0円以上で入力してください。')
    if (!Number.isInteger(bulletsNumber) || bulletsNumber < 1) return setMessage('使用エントリー数は1以上の整数で入力してください。')
    if (totalNumber !== null && (!Number.isFinite(totalNumber) || totalNumber < 0)) return setMessage('総参加費は0円以上で入力してください。')
    if (!Number.isFinite(prizeNumber) || prizeNumber < 0) return setMessage('獲得額（相当額）は0円以上で入力してください。')
    if (bbNumber !== null && (!Number.isFinite(bbNumber) || bbNumber <= 0)) return setMessage('参加時BBは0より大きい数値で入力してください。')

    setIsSaving(true)
    setMessage('保存中...')
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) { setIsSaving(false); return navigate('/login') }

    const { error } = await supabase.from('poker_results').update({
      tournament_name: name,
      played_at: playedAt,
      venue: venue.trim() || null,
      rank: rankNumber,
      rank_unknown: rankUnknown,
      entry_count: entryCountNumber,
      is_itm: isItm,
      entry_fee: entryFeeNumber,
      bullets: bulletsNumber,
      total_entry_fee: totalNumber,
      prize_amount: prizeNumber,
      entry_timing: entryTiming,
      entry_bb: bbNumber,
      game_type: gameType || null,
      prize_description: prizeDescription.trim() || null,
      memo: memo.trim() || null,
      is_public: isPublic,
      is_featured: isPublic ? isFeatured : false,
    }).eq('id', id).eq('user_id', user.id)

    if (error) {
      console.error(error)
      setMessage(`保存に失敗しました：${error.message}`)
      setIsSaving(false)
      return
    }
    navigate('/profile')
  }

  const handleDelete = async () => {
    if (!id || !window.confirm('このトーナメント記録を削除しますか？\nこの操作は元に戻せません。')) return
    setIsDeleting(true)
    setMessage('削除中...')
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) { setIsDeleting(false); return navigate('/login') }
    const { error } = await supabase.from('poker_results').delete().eq('id', id).eq('user_id', user.id)
    if (error) {
      console.error(error)
      setMessage(`削除に失敗しました：${error.message}`)
      setIsDeleting(false)
      return
    }
    navigate('/profile')
  }

  const labelStyle: React.CSSProperties = { marginBottom: '8px', fontSize: '13px', fontWeight: 700 }
  const optionalStyle: React.CSSProperties = { marginLeft: '5px', color: '#777', fontWeight: 400 }
  const choiceButton = (selected: boolean): React.CSSProperties => ({ flex: 1, minHeight: '44px', padding: '10px 12px', background: selected ? '#f5f5f5' : '#111', color: selected ? '#000' : '#aaa', border: selected ? '1px solid #f5f5f5' : '1px solid #2d2d2d', borderRadius: '12px', fontSize: '13px', fontWeight: 700 })

  if (isLoading) return <main className="app"><div className="card"><p style={{ color:'#777', textAlign:'center', paddingTop:'80px' }}>読み込み中...</p></div></main>

  return (
    <main className="app">
      <div className="card" style={{ paddingTop: 0 }}>
        <header style={{ position:'sticky', top:0, zIndex:20, margin:'0 -20px', padding:'15px 20px', display:'flex', alignItems:'center', gap:'12px', background:'rgba(0,0,0,.95)', borderBottom:'1px solid #242424', backdropFilter:'blur(14px)' }}>
          <button type="button" onClick={() => navigate('/profile')} aria-label="戻る" style={{ width:'34px', height:'34px', padding:0, display:'flex', alignItems:'center', justifyContent:'center', background:'transparent', color:'#fff', borderRadius:'50%', fontSize:'27px' }}>‹</button>
          <div style={{ fontSize:'18px', fontWeight:800 }}>トーナメント記録を編集</div>
        </header>

        <div style={{ padding:'24px 0 8px' }}>
          <div style={{ fontSize:'22px', fontWeight:800 }}>トーナメント記録</div>
          <p style={{ margin:'8px 0 0', color:'#777', fontSize:'13px' }}>登録済みの記録を編集できます。</p>
        </div>

        <div style={{ display:'flex', flexDirection:'column', gap:'22px', marginTop:'22px' }}>
          <label><div style={labelStyle}>トーナメント名<span style={optionalStyle}>必須</span></div><input value={tournamentName} onChange={e=>setTournamentName(e.target.value)} maxLength={100} /></label>
          <label><div style={labelStyle}>開催日<span style={optionalStyle}>必須</span></div><input type="date" value={playedAt} onChange={e=>setPlayedAt(e.target.value)} /></label>
          <label><div style={labelStyle}>店舗・シリーズ<span style={optionalStyle}>任意</span></div><input placeholder="例：JOPT / Poker Room ○○" value={venue} onChange={e=>setVenue(e.target.value)} maxLength={100} /></label>

          <div><div style={labelStyle}>順位<span style={optionalStyle}>必須</span></div><div style={{ display:'grid', gridTemplateColumns:'1fr auto', gap:'10px' }}><input type="number" min="1" placeholder="例：3" value={rank} disabled={rankUnknown} onChange={e=>setRank(e.target.value)} /><button type="button" onClick={()=>{const n=!rankUnknown;setRankUnknown(n);if(n)setRank('')}} style={{ padding:'0 15px', background:rankUnknown?'#fff':'#111', color:rankUnknown?'#000':'#aaa', border:'1px solid #444', borderRadius:'12px', fontWeight:700 }}>順位不明</button></div></div>
          <label><div style={labelStyle}>参加人数<span style={optionalStyle}>任意</span></div><input type="number" min="1" placeholder="例：250" value={entryCount} onChange={e=>setEntryCount(e.target.value)} /></label>

          <button type="button" onClick={()=>setIsItm(!isItm)} style={{ padding:'14px', background:isItm?'#171717':'#0d0d0d', color:'#fff', border:isItm?'1px solid #666':'1px solid #2d2d2d', borderRadius:'14px', textAlign:'left', fontWeight:700 }}>{isItm?'✓ ':''}インマネした</button>

          <div style={{ height:'1px', background:'#242424' }} />
          <div style={{ fontSize:'16px', fontWeight:800 }}>参加費・獲得額</div>
          <label><div style={labelStyle}>参加費<span style={optionalStyle}>1エントリーあたり</span></div><input type="number" min="0" value={entryFee} onChange={e=>setEntryFee(e.target.value)} /></label>
          <label><div style={labelStyle}>使用エントリー数<span style={optionalStyle}>何機</span></div><input type="number" min="1" step="1" value={bullets} onChange={e=>setBullets(e.target.value)} /></label>

          <div><div style={labelStyle}>総参加費</div>{!totalFeeEdited ? <div style={{ padding:'13px 14px', display:'flex', justifyContent:'space-between', alignItems:'center', background:'#0d0d0d', border:'1px solid #242424', borderRadius:'12px' }}><div><strong>{formatYen(calculatedTotalFee())}</strong><div style={{ color:'#666', fontSize:'11px' }}>参加費 × 使用エントリー数</div></div><button type="button" onClick={()=>{setTotalEntryFee(calculatedTotalFee());setTotalFeeEdited(true)}} style={{ padding:'8px 11px', background:'#181818', color:'#ddd', border:'1px solid #333', borderRadius:'999px' }}>修正する</button></div> : <><input type="number" min="0" value={totalEntryFee} onChange={e=>setTotalEntryFee(e.target.value)} /><button type="button" onClick={()=>{setTotalFeeEdited(false);setTotalEntryFee('')}} style={{ marginTop:'8px', padding:0, background:'transparent', color:'#888' }}>自動計算に戻す</button></>}</div>

          <label><div style={labelStyle}>獲得額（相当額）</div><input type="number" min="0" value={prizeAmount} onChange={e=>setPrizeAmount(e.target.value)} /><div style={{ marginTop:'7px', color:'#666', fontSize:'11px' }}>チケット・商品などを獲得した場合は、その相当額を入力してください。</div></label>

          <div style={{ height:'1px', background:'#242424' }} />
          <div><div style={labelStyle}>参加タイミング</div><div style={{ display:'flex', gap:'8px' }}><button type="button" onClick={()=>setEntryTiming('early')} style={choiceButton(entryTiming==='early')}>開始付近</button><button type="button" onClick={()=>setEntryTiming('middle')} style={choiceButton(entryTiming==='middle')}>中盤</button><button type="button" onClick={()=>setEntryTiming('late')} style={choiceButton(entryTiming==='late')}>レイト付近</button></div></div>

          <div style={{ height:'1px', background:'#242424' }} />
          <div><button type="button" onClick={()=>setShowDetails(!showDetails)} style={{ width:'100%', padding:'13px 0', display:'flex', justifyContent:'space-between', background:'transparent', color:'#fff', fontWeight:800 }}><span>詳細を追加</span><span>{showDetails?'⌃':'⌄'}</span></button>{showDetails && <div style={{ display:'flex', flexDirection:'column', gap:'18px', paddingTop:'10px' }}><label><div style={labelStyle}>参加時BB<span style={optionalStyle}>任意</span></div><input type="number" min="0.1" step="0.1" value={entryBb} onChange={e=>setEntryBb(e.target.value)} /></label><label><div style={labelStyle}>ゲーム種別<span style={optionalStyle}>任意</span></div><select value={gameType} onChange={e=>setGameType(e.target.value)}><option value="">選択しない</option><option value="NLH">NLH</option><option value="PLO">PLO</option><option value="MIX">MIX</option><option value="OTHER">その他</option></select></label><label><div style={labelStyle}>獲得内容<span style={optionalStyle}>任意</span></div><input placeholder="例：JOPT Main Event Ticket" value={prizeDescription} onChange={e=>setPrizeDescription(e.target.value)} maxLength={150} /></label></div>}</div>

          <label><div style={labelStyle}>メモ<span style={optionalStyle}>任意</span></div><textarea value={memo} onChange={e=>setMemo(e.target.value)} maxLength={500} rows={4} /></label>

          <div style={{ height:'1px', background:'#242424' }} />
          <div><div style={labelStyle}>公開設定</div><div style={{ display:'flex', gap:'10px' }}><button type="button" onClick={()=>handlePublicChange(false)} style={choiceButton(!isPublic)}>🔒 非公開</button><button type="button" onClick={()=>handlePublicChange(true)} style={choiceButton(isPublic)}>🌐 公開</button></div><div style={{ marginTop:'9px', color:'#666', fontSize:'12px' }}>公開設定はあとから変更できます。</div></div>

          {isPublic && <button type="button" onClick={()=>setIsFeatured(!isFeatured)} style={{ padding:'14px', background:isFeatured?'#171717':'#0d0d0d', color:'#fff', border:isFeatured?'1px solid #666':'1px solid #2d2d2d', borderRadius:'14px', textAlign:'left', fontWeight:700 }}>{isFeatured?'✓ ':''}主なトーナメント実績に表示</button>}
        </div>

        {message && <div style={{ marginTop:'18px', color:message==='保存中...'||message==='削除中...'?'#777':'#ff7777', fontSize:'12px', textAlign:'center' }}>{message}</div>}
        <button type="button" onClick={handleSave} disabled={isSaving||isDeleting} style={{ width:'100%', marginTop:'26px', padding:'14px 18px', background:'#fff', color:'#000', borderRadius:'999px', fontSize:'15px', fontWeight:800 }}>{isSaving?'保存中...':'変更を保存'}</button>
        <button type="button" onClick={handleDelete} disabled={isSaving||isDeleting} style={{ width:'100%', marginTop:'12px', padding:'13px 18px', background:'transparent', color:'#ff6868', border:'1px solid #3a2020', borderRadius:'999px', fontSize:'14px', fontWeight:700 }}>{isDeleting?'削除中...':'このトーナメント記録を削除'}</button>
      </div>
    </main>
  )
}

export default PokerResultEdit
