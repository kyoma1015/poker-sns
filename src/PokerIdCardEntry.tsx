import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from './supabase'

export default function PokerIdCardEntry({ userId, own = false }: {userId: string; own?: boolean}) {
  const navigate = useNavigate()
  const [publicCard, setPublicCard] = useState(false)
  useEffect(() => {
    if (own || !userId) return
    let alive = true
    void supabase.from('poker_id_cards').select('user_id').eq('user_id',userId).eq('is_public',true).maybeSingle().then(({data}) => {
      if (alive) setPublicCard(!!data)
    })
    return () => {alive=false}
  },[userId,own])
  if (!own && !publicCard) return null
  return <button type="button" onClick={() => navigate(own ? '/profile/card' : '/player/' + encodeURIComponent(userId) + '/card')}
    style={{display:'flex',width:'100%',textAlign:'left',alignItems:'center',gap:12,padding:'15px 16px',margin:'18px 0 4px',background:'#111',border:'1px solid #353535',borderRadius:14,color:'#fff'}}>
    <span aria-hidden="true" style={{background:'#f9e2eb',color:'#723e54',borderRadius:9,padding:10,fontSize:19}}>♠</span>
    <span style={{flex:1,minWidth:0}}><strong style={{display:'block',fontSize:14}}>{own?'Poker IDカードを作成・編集':'Poker IDカードを見る'}</strong>
      <span style={{display:'block',fontSize:11,color:'#999',marginTop:5}}>{own?'進捗・プレビュー・テーマ・公開設定':'このプレイヤーが公開したカードを表示'}</span>
    </span>
    <span aria-hidden="true" style={{color:'#aaa'}}>›</span>
  </button>
}
