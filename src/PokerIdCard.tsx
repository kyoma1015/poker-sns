import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { supabase } from './supabase'
import { profileCardUrl, renderPokerIdCard, savePokerIdImage } from './pokerIdCardExport'

type ProfileData = {
  id: string; poker_id: string; display_name: string; avatar_url?: string | null
  poker_started_year?: number | null; poker_started_month?: number | null; poker_years?: number | null
  main_game?: string | null; main_play?: string | null; poker_frequency?: string | null
  hobbies?: string[] | null; poker_meaning?: string | null; poker_meaning_detail?: string | null; my_hand_cards?: string[] | null; my_hand_reason?: string | null
  activity_areas?: string[] | null
}
type Animal = { result_type_key: string; animal_name_ja: string; catchphrase: string; result_id?: string }
type DiagnosisDetail = { description: string; behavior_text: string; strength_text: string; weakness_text: string; perceived_text: string; best_situation_text: string }
type Achievement = { id: string; source: 'past' | 'regular'; title: string; rank: number | null; entryCount: number | null; year: string; is_public: boolean }
type CardConfig = { user_id: string; theme: string; is_public: boolean; updated_at?: string }
const themes = [
  { key: 'classic', label: 'Classic', bg: '#E8EAED', panel: '#F8F9FA', line: '#B3BAC5', accent: '#626A75' },
  { key: 'ice', label: 'Ice Blue', bg: '#DBEDF9', panel: '#F3FAFF', line: '#A6CADE', accent: '#527FA3' },
  { key: 'navy', label: 'Mist Navy', bg: '#DDE4F0', panel: '#F4F6FC', line: '#AFBED5', accent: '#566B8C' },
  { key: 'mint', label: 'Mint', bg: '#D9F2E9', panel: '#F5FFFA', line: '#A3D4C1', accent: '#478B78' },
  { key: 'sage', label: 'Sage', bg: '#E3ECD9', panel: '#F8FCF3', line: '#BACDAF', accent: '#718766' },
  { key: 'lavender', label: 'Lavender', bg: '#EBE1F8', panel: '#FBF7FF', line: '#C8B5E0', accent: '#8970AD' },
  { key: 'blossom', label: 'Blossom', bg: '#F9E2EB', panel: '#FFF7FA', line: '#DDB7C8', accent: '#B77B93' },
  { key: 'cream', label: 'Cream', bg: '#FFF0CE', panel: '#FFFAEE', line: '#E1C992', accent: '#AC874A' },
] as const
const required: { key: string; label: string; check: (p: ProfileData, a: Animal | null) => boolean; link: string }[] = [
  { key: 'identity', label: '表示名・Poker ID', check: p => !!(p.display_name?.trim() && p.poker_id?.trim()), link: '/profile/edit' },
  { key: 'experience', label: 'ポーカー歴', check: p => !!((p.poker_started_year && p.poker_started_month) || p.poker_years), link: '/profile/edit' },
  { key: 'game', label: 'メイン種目', check: p => !!p.main_game, link: '/profile/edit' },
  { key: 'play', label: 'メインプレイ', check: p => !!p.main_play, link: '/profile/edit' },
  { key: 'frequency', label: 'ポーカー頻度', check: p => !!p.poker_frequency, link: '/profile/edit' },
  { key: 'hobbies', label: 'ポーカー以外の趣味', check: p => !!p.hobbies?.length, link: '/profile/edit' },
  { key: 'meaning', label: 'あなたにとってポーカーとは？', check: p => !!p.poker_meaning?.trim(), link: '/profile/edit#poker-meaning' },
  { key: 'hand', label: 'マイハンド', check: p => p.my_hand_cards?.length === 2, link: '/profile/edit#my-hand' },
  { key: 'animal', label: 'プレイヤータイプ診断', check: (_p, a) => !!a, link: '/player-type' },
]
export default function PokerIdCard() {
  const navigate = useNavigate()
  const { userId } = useParams()
  const [viewerId, setViewerId] = useState('')
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [animal, setAnimal] = useState<Animal | null>(null)
  const [diagnosisDetail, setDiagnosisDetail] = useState<DiagnosisDetail | null>(null)
  const [achievements, setAchievements] = useState<Achievement[]>([])
  const [highlight, setHighlight] = useState<{ source_type: string; source_id: string } | null>(null)
  const [config, setConfig] = useState<CardConfig | null>(null)
  const [themeKey, setThemeKey] = useState('classic')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [previewError, setPreviewError] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const own = !userId || (!!viewerId && userId === viewerId)
  const targetId = userId || viewerId

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true); setError('')
      const { data: { user } } = await supabase.auth.getUser()
      if (cancelled) return
      setViewerId(user?.id ?? '')
      const id = userId || user?.id
      if (!id) { navigate('/login'); return }
      const [p, publicAnimal, ownAnimal, past, regular, hi, card] = await Promise.all([
        supabase.from('profiles').select('*').eq('id', id).maybeSingle(),
        supabase.rpc('get_public_latest_player_type_v2', { p_user_id: id }),
        user?.id === id ? supabase.rpc('get_my_latest_player_type_v2') : Promise.resolve({ data: null, error: null }),
        supabase.from('poker_past_achievements').select('id,tournament_name,event_year,rank,entry_count,is_public').eq('user_id', id),
        supabase.from('poker_results').select('id,tournament_name,played_at,rank,entry_count,rank_unknown,is_featured,is_public').eq('user_id', id).eq('is_featured', true),
        supabase.from('poker_achievement_highlights').select('source_type,source_id').eq('user_id', id).maybeSingle(),
        supabase.from('poker_id_cards').select('*').eq('user_id', id).maybeSingle(),
      ])
      if (cancelled) return
      if (p.error || !p.data) { setError('プロフィールを取得できませんでした'); setLoading(false); return }
      setProfile(p.data as ProfileData)
      const ar = (user?.id === id ? ownAnimal.data : publicAnimal.data) as Animal[] | null
      setAnimal(ar?.[0] ?? null)
      setDiagnosisDetail(null)
      const diagnosisId = (ar?.[0] as { result_id?: string } | undefined)?.result_id
      if (diagnosisId) {
        const detail = await supabase.rpc('get_player_type_v2_result_detail', { p_result_id: diagnosisId })
        if (!cancelled && !detail.error) setDiagnosisDetail((detail.data?.[0] ?? null) as DiagnosisDetail | null)
      }
      const visible = (user?.id === id)
      const a: Achievement[] = [
        ...((past.data ?? []) as {id:string;tournament_name:string;event_year:number;rank:number;entry_count:number|null;is_public:boolean}[]).filter(x=>visible || x.is_public).map(x=>({id:x.id,source:'past' as const,title:x.tournament_name,rank:x.rank,entryCount:x.entry_count,year:String(x.event_year),is_public:x.is_public})),
        ...((regular.data ?? []) as {id:string;tournament_name:string;played_at:string;rank:number|null;entry_count:number|null;rank_unknown:boolean;is_public:boolean}[]).filter(x=>x.is_public).map(x=>({id:x.id,source:'regular' as const,title:x.tournament_name,rank:x.rank_unknown?null:x.rank,entryCount:x.entry_count,year:(x.played_at||'').slice(0,4),is_public:x.is_public}))
      ]
      setAchievements(a.filter(x=>x.is_public))
      setHighlight(hi.data ?? null)
      if (!card.error && card.data) { setConfig(card.data as CardConfig); setThemeKey(card.data.theme || 'classic') }
      else if (card.error) setError('カードの公開設定を取得できません。DBマイグレーションの適用を確認してください。')
      setLoading(false)
    }
    void load()
    return () => { cancelled = true }
  }, [userId,navigate])
  const checks = useMemo(() => profile ? required.map(x=>({...x,done:x.check(profile,animal)})) : [], [profile,animal])
  const count = checks.filter(x=>x.done).length
  const ready = count === required.length
  const theme = themes.find(x=>x.key===themeKey) ?? themes[0]
  const ordered = useMemo(() => [...achievements].sort((a,b) => {
    const am = highlight?.source_type===a.source && highlight.source_id===String(a.id)
    const bm = highlight?.source_type===b.source && highlight.source_id===String(b.id)
    return Number(bm)-Number(am)
  }),[achievements,highlight])
  const isPublic = !!config?.is_public
  const canView = own || isPublic
  // The on-screen preview uses the exact same PNG renderer as the downloaded image.
  useEffect(() => {
    if (!profile || !targetId || (!own && !config?.is_public)) {
      setPreviewUrl(null)
      return
    }
    let cancelled = false
    let currentUrl: string | null = null
    setPreviewError('')
    setPreviewUrl(null)
    void renderPokerIdCard({ profile, animal, diagnosisDetail, achievements: ordered, theme, userId: targetId })
      .then(blob => {
        if (cancelled) return
        currentUrl = URL.createObjectURL(blob)
        setPreviewUrl(currentUrl)
      })
      .catch(e => { if (!cancelled) setPreviewError(e instanceof Error ? e.message : String(e)) })
    return () => { cancelled = true; if (currentUrl) URL.revokeObjectURL(currentUrl) }
  }, [profile, animal, diagnosisDetail, ordered, theme, targetId, own, config?.is_public])
  const exportImage = async (share: boolean) => {
    if (!profile || !targetId || exporting || (own && !ready)) return
    setExporting(true); setError(''); setNotice('')
    try {
      const blob = await renderPokerIdCard({ profile, animal, diagnosisDetail, achievements: ordered, theme, userId: targetId })
      if (share) {
        const file = new File([blob], 'PokerID_' + profile.poker_id + '.png', { type: 'image/png' })
        if (navigator.canShare?.({files:[file]}) && navigator.share) {
          try { await navigator.share({ files:[file], title:'Poker IDカード', text:'私のPoker IDカード！ #PokerID #ポーカー' }) }
          catch (e) { if ((e as Error).name !== 'AbortError') throw e }
        } else {
          savePokerIdImage(blob,profile.poker_id)
          const intent = new URL('https://twitter.com/intent/tweet')
          intent.searchParams.set('text','私のPoker IDカード！ #PokerID #ポーカー')
          intent.searchParams.set('url',profileCardUrl(targetId))
          window.open(intent.toString(),'_blank','noopener,noreferrer')
          setNotice('画像を保存しました。Xの投稿画面で保存した画像を添付してください。')
        }
      } else { savePokerIdImage(blob,profile.poker_id); setNotice('カード画像を保存しました') }
    } catch (e) { setError('カード画像の作成・共有に失敗しました：'+(e instanceof Error?e.message:String(e))) }
    finally { setExporting(false) }
  }
  const saveConfig = async (next: {theme:string;is_public:boolean}) => {
    if (!own || !viewerId || saving) return
    setSaving(true);setError('');setNotice('')
    const {error:e} = await supabase.from('poker_id_cards').upsert({user_id:viewerId,theme:next.theme,is_public:next.is_public,updated_at:new Date().toISOString()},{onConflict:'user_id'})
    if (e) setError('カードの保存に失敗しました：'+e.message)
    else {setConfig({user_id:viewerId,...next});setThemeKey(next.theme);setNotice('保存しました')}
    setSaving(false)
  }
  if (loading) return <main style={{padding:20,color:'#aaa'}}>Poker IDカードを読み込み中...</main>
  if (!profile || !canView) return <main style={{padding:20}}><h2>カードは公開されていません</h2><button onClick={()=>navigate(-1)}>戻る</button></main>
  return <main style={{maxWidth:600,margin:'0 auto',padding:'20px 16px 140px',color:'#fff'}}>
    <button type="button" onClick={()=>navigate(-1)} style={{background:'transparent',color:'#aaa',padding:'8px 0'}}>← 戻る</button>
    <h1 style={{fontSize:24,margin:'14px 0'}}>Poker IDカード</h1>
    {error && <p role="alert" style={{color:'#ff9999'}}>{error}</p>}
    {notice && <p role="status" style={{color:'#b5ddb5'}}>{notice}</p>}
    {own && <section style={{background:'#141414',border:'1px solid #333',borderRadius:16,padding:16,marginBottom:22}}>
      <div style={{display:'flex',justifyContent:'space-between',fontWeight:800}}>カード作成進捗 <span>{count} / {required.length}</span></div>
      <div style={{height:7,background:'#333',borderRadius:8,margin:'13px 0 18px',overflow:'hidden'}}><div style={{background:'#f2d3e1',width:(count/required.length*100)+'%',height:'100%'}} /></div>
      {!ready && <p style={{fontSize:12,color:'#aaa'}}>未登録項目をタップして登録すると、カードを公開できます。プレビューはいつでも確認できます。</p>}
      <div style={{display:'grid',gap:6}}>{checks.map(item=><button type="button" key={item.key} onClick={()=>!item.done&&navigate(item.link)} disabled={item.done} style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'9px 10px',background:'#1f1f1f',border:'1px solid #303030',color:item.done?'#9ea7a0':'#fff',textAlign:'left',borderRadius:8}}><span>{item.done?'✓':'○'} {item.label}</span>{!item.done&&<span style={{fontSize:12}}>登録する ›</span>}</button>)}</div>
      <p style={{color:'#999',fontSize:11,marginBottom:0}}>プロフィール画像・活動エリア・大会実績は任意です。</p>
    </section>}
    {own && <section style={{marginBottom:18}}>
      <h2 style={{fontSize:15,marginBottom:12}}>カードカラー</h2>
      <div style={{display:'grid',gridTemplateColumns:'repeat(4,minmax(0,1fr))',gap:8}}>{themes.map(t=><button type="button" key={t.key} onClick={()=>{setThemeKey(t.key);setNotice('')}} style={{background:t.bg,color:'#202632',border:themeKey===t.key?'3px solid #fff':'3px solid #555',borderRadius:12,padding:'16px 2px',fontSize:11,fontWeight:800}}>{t.label}</button>)}</div>
    </section>}
    <section aria-label="Poker IDカードプレビュー" style={{aspectRatio:'4/5',width:'100%',background:theme.bg,borderRadius:13,overflow:'hidden',display:'grid',placeItems:'center'}}>
      {previewUrl ? <img src={previewUrl} alt="Poker IDカードの完成プレビュー。保存するPNG画像と同じレイアウトです。" style={{display:'block',width:'100%',height:'100%',objectFit:'contain'}} /> : <div style={{padding:20,textAlign:'center',color:'#35404d'}}>{previewError ? '画像プレビューの生成に失敗しました：'+previewError : 'カード画像を生成中…'}</div>}
    </section>
    {own && <section style={{marginTop:18,background:'#141414',border:'1px solid #333',borderRadius:14,padding:16}}>
      <h2 style={{fontSize:16,margin:'0 0 8px'}}>公開設定</h2>
      <p style={{fontSize:12,color:'#aaa'}}>カードは自分で公開するまで他人には表示されません。公開後もいつでも非公開にできます。</p>
      {!ready && <p style={{color:'#eccbaa',fontSize:12}}>あと{required.length-count}項目で公開可能になります。</p>}
      <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
        <button type="button" disabled={saving} onClick={()=>void saveConfig({theme:themeKey,is_public:isPublic})} style={{padding:'11px 14px',borderRadius:8,background:'#333',color:'#fff'}}>カラーを保存</button>
        <button type="button" disabled={saving||(!ready&&!isPublic)} onClick={()=>void saveConfig({theme:themeKey,is_public:!isPublic})} style={{padding:'11px 14px',borderRadius:8,background:isPublic?'#393939':'#fff',color:isPublic?'#fff':'#111'}}>{isPublic?'カードを非公開にする':'カードを公開する'}</button>
      </div>
      <p style={{fontSize:12,color:'#999'}}>現在の状態：{isPublic?'公開中':'非公開'}</p>
    </section>}
    {!own && <p style={{color:'#aaa',fontSize:12,marginTop:16}}>このカードの内容は公開プロフィールに基づいています。</p>}
    <section style={{display:'flex',gap:10,marginTop:20,flexWrap:'wrap'}}>
      <button type="button" disabled={exporting || (own&&!ready)} onClick={()=>void exportImage(false)} style={{padding:'14px 17px',borderRadius:10,background:'#fff',color:'#111',fontWeight:800,opacity:exporting||(own&&!ready)?.5:1}}>{exporting?'画像を作成中…':'PNG画像を保存'}</button>
      <button type="button" disabled={exporting || (own&&!ready)} onClick={()=>void exportImage(true)} style={{padding:'14px 17px',borderRadius:10,background:'#222',color:'#fff',border:'1px solid #777',fontWeight:800,opacity:exporting||(own&&!ready)?.5:1}}>X・SNSに共有</button>
    </section>
    {own&&!ready&&<p style={{color:'#aaa',fontSize:12}}>必要項目を登録すると保存・共有が利用できます。プレビューとQRコードは先に確認できます。</p>}
    <p style={{color:'#888',fontSize:11,marginTop:14}}>スマホの共有先が画像を受け取れない場合は、PNG保存後にXの投稿画面を開きます。</p>
  </main>
}
