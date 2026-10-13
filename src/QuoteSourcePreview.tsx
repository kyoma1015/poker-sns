import type { CSSProperties } from 'react'

export type QuoteSource = {
  id: string
  user_id: string
  content: string
  profile?: { display_name: string; poker_id: string }
  image_urls?: string[] | null
  result_type?: string | null
  resultData?: Record<string, unknown> | null
  playerTypeData?: { animal_name_ja: string; catchphrase: string; result_type_key: string } | null
  style_snapshot?: { count: number; aggression: number; looseness: number; captured_at: string } | null
}

const cardStyle: CSSProperties = { padding: 11, border: '1px solid #484848', borderRadius: 10, background: '#242424', marginTop: 9, fontSize: 12, lineHeight: 1.5, color: '#eee', overflowWrap: 'anywhere' }
const labelStyle: CSSProperties = { fontSize: 11, color: '#c4ae79', marginBottom: 5, fontWeight: 700 }
const show = (value: unknown) => value === null || value === undefined || value === '' ? '—' : String(value)

export default function QuoteSourcePreview({ source, onOpen, compact = false }: { source: QuoteSource | null | undefined; onOpen?: () => void; compact?: boolean }) {
  if (!source) return <div style={{ ...cardStyle, color: '#999' }}>元の投稿は表示できません</div>
  const result = source.resultData || null
  const detailEntries = result && Object.entries(result).filter(([key, value]) =>
    !['id','user_id','created_at','updated_at','image_urls'].includes(key) && value !== null && value !== undefined && value !== ''
  ).slice(0, compact ? 5 : 8)
  const resultNames: Record<string, string> = { tournament: '🏆 トーナメント戦績', amusement: '♠ リングゲーム戦績', cash: '♦ キャッシュゲーム戦績', player_type: '🃏 プレイヤータイプ診断' }
  const fieldNames: Record<string,string> = { tournament_name:'大会名', rank:'順位', entry_count:'参加人数', is_itm:'入賞', total_entry_fee:'参加費合計', prize_amount:'獲得賞金', venue:'店舗・会場', played_at:'プレイ日', game_type:'ゲーム', small_blind:'SB', big_blind:'BB', starting_stack:'開始スタック', ending_stack:'終了スタック', profit_amount:'収支', profit_jpy:'円換算収支', play_minutes:'プレイ時間', play_type:'プレイ形式' }
  return <div role={onOpen ? 'link' : undefined} tabIndex={onOpen ? 0 : undefined}
    onClick={onOpen} onKeyDown={onOpen ? event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onOpen() } } : undefined}
    style={{ padding: compact ? 10 : 12, margin: '8px 0 12px', background: '#171717', border: '1px solid #484848', borderRadius: 12, color: '#eee', cursor: onOpen ? 'pointer' : 'default', textAlign: 'left', maxWidth: '100%', minWidth: 0 }}>
    <div style={{ fontSize: 12, fontWeight: 750, overflowWrap: 'anywhere' }}>{source.profile?.display_name || 'Player'} <span style={{ color: '#aaa', fontSize: 11, fontWeight: 400 }}>@{source.profile?.poker_id || 'unknown'}</span></div>
    {!!source.content && <div style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', fontSize: compact ? 12 : 13, lineHeight: 1.55, marginTop: 7 }}>{source.content}</div>}
    {!!source.image_urls?.length && <div style={{ display: 'grid', gridTemplateColumns: source.image_urls.length === 1 ? 'minmax(0,1fr)' : 'repeat(2,minmax(0,1fr))', gap: 5, marginTop: 8 }}>
      {source.image_urls.slice(0, 4).map((url,index) => <img key={`${url}-${index}`} src={url} alt={`引用元の画像${index+1}`} loading="lazy" style={{ display: 'block', width: '100%', maxHeight: compact ? 128 : 185, aspectRatio: source.image_urls?.length === 1 ? '16/9' : '4/3', objectFit: 'cover', borderRadius: 7 }}/>)}</div>}
    {source.result_type === 'player_type' && <div style={cardStyle}>
      <div style={labelStyle}>{resultNames.player_type}</div>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
        {source.playerTypeData?.result_type_key && <img src={`/animals/${source.playerTypeData.result_type_key}.png`} alt="診断タイプ" style={{ width: compact ? 64 : 82, height: compact ? 64 : 82, borderRadius: 10, objectFit: 'cover' }}/>}
        <div style={{ minWidth: 0 }}><strong style={{ fontSize: compact ? 14 : 16 }}>{source.playerTypeData?.animal_name_ja || 'プレイヤータイプ診断'}</strong><div style={{ color: '#c8c8c8', marginTop: 3 }}>{source.playerTypeData?.catchphrase || ''}</div></div>
      </div>
    </div>}
    {source.result_type && source.result_type !== 'player_type' && <div style={cardStyle}>
      <div style={labelStyle}>{resultNames[source.result_type] || '♠ 戦績'}</div>
      {detailEntries && detailEntries.length > 0 ? <div style={{ display:'grid', gridTemplateColumns:'auto minmax(0,1fr)', columnGap: 12, rowGap: 5 }}>
        {detailEntries.map(([key,value]) => <div key={key} style={{ display:'contents' }}><span style={{ color:'#aaa' }}>{fieldNames[key] || key}</span><span style={{ fontWeight:600, overflowWrap:'anywhere' }}>{typeof value === 'boolean' ? (value ? 'はい' : 'いいえ') : show(value)}</span></div>)}
      </div> : <span style={{ color:'#aaa' }}>詳細は元の投稿で確認できます</span>}
    </div>}
    {!!source.style_snapshot && <div style={cardStyle}><div style={labelStyle}>♟ 他者評価カード</div><div>評価人数 {source.style_snapshot.count}人　アグレッション {source.style_snapshot.aggression}　ルースネス {source.style_snapshot.looseness}</div></div>}
    {onOpen && <div style={{ marginTop: 8, color:'#b8b8b8', fontSize:11 }}>元の投稿を見る →</div>}
  </div>
}
