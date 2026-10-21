import { createPollRequest, pollDisplayResult, pollVoteRequest } from './interactiveRequests'
import { useEffect, useState } from 'react'
import { supabase } from './supabase'

export type InteractiveItem = {
  post_id: string
  kind: 'poll' | 'question'
  options: string[]
  closes_at: string | null
  is_anonymous: boolean
}
export type InteractiveResult = { post_id: string; total_votes: number; vote_counts: Record<string,number>; answers: {answer:string;is_anonymous?:boolean;poker_id?:string;display_name?:string;avatar_url?:string}[]; my_option_index: number | null; has_responded: boolean; voters: {option_index:number;poker_id?:string;display_name?:string;avatar_url?:string}[] }

export function InteractiveComposer({ onCreated }: { onCreated: () => Promise<void> }) {
  const kind: 'poll' = 'poll'
  const [content, setContent] = useState('')
  const [options, setOptions] = useState(['',''])
  const [hours, setHours] = useState(24)
  const [pollAnonymous, setPollAnonymous] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const submit = async () => {
    if (busy) return
    setBusy(true); setError('')
    try {
      const request = createPollRequest(kind, content, options, hours, pollAnonymous)
      const { error: failure } = await supabase.rpc('create_interactive_post_v4', request)
      if (failure) throw failure
      setContent(''); setOptions(['',''])
      await onCreated()
    } catch (e) { setError(e instanceof Error ? e.message : '投稿に失敗しました') }
    finally { setBusy(false) }
  }
  const inputStyle = { width:'100%', boxSizing:'border-box' as const, padding:10, borderRadius:8, background:'#202020', color:'#fff', border:'1px solid #444' }
  return <section style={{padding:16,border:'1px solid #333',borderRadius:12,marginBottom:16,color:'#fff'}}>
    <div style={{fontSize:14,fontWeight:700,marginBottom:12}}>📊 アンケートを作成</div>
    <textarea aria-label="質問内容" value={content} onChange={e=>setContent(e.target.value)} maxLength={500} placeholder="みんなに聞きたいことは？" style={{...inputStyle,minHeight:72}} />
    {<>
      <div style={{display:'grid',gap:8,marginTop:10}}>{options.map((v,i)=><input key={i} aria-label={`選択肢${i+1}`} maxLength={80} placeholder={`${String.fromCharCode(65+i)}：選択肢${i+1}`} value={v} onChange={e=>setOptions(a=>a.map((s,j)=>j===i?e.target.value:s))} style={inputStyle}/>)}</div>
      <div style={{display:'flex',gap:8,alignItems:'center',marginTop:10}}>
        {options.length<4 && <button type="button" onClick={()=>setOptions(a=>[...a,''])} style={{width:'auto',background:'#30343b',color:'#eee',border:'1px solid #555',borderRadius:8,padding:'7px 12px'}}>＋ 選択肢</button>}
        {options.length>2 && <button type="button" onClick={()=>setOptions(a=>a.slice(0,-1))} style={{width:'auto',background:'#30343b',color:'#eee',border:'1px solid #555',borderRadius:8,padding:'7px 12px'}}>− 削除</button>}
        <label style={{fontSize:13}}>投票期限 <select value={hours} onChange={e=>setHours(Number(e.target.value))} style={{background:'#222',color:'#fff',padding:6}}>{[1,6,24,72,168].map(h=><option key={h} value={h}>{h<24?`${h}時間`:`${h/24}日`}</option>)}</select></label>
      </div>
      <div style={{display:'flex',gap:8,marginTop:10}}>{([{anonymous:false,label:'記名投票'},{anonymous:true,label:'匿名投票'}] as const).map(mode=><button key={mode.label} type="button" aria-pressed={pollAnonymous===mode.anonymous} onClick={()=>setPollAnonymous(mode.anonymous)} style={{width:'auto',background:pollAnonymous===mode.anonymous?'#393939':'#181818',color:'#eee',border:'1px solid '+(pollAnonymous===mode.anonymous?'#ddd':'#444'),padding:'8px 12px',borderRadius:9}}>{mode.label}</button>)}</div>
    </>}
    <p style={{fontSize:12,color:'#aaa'}}>投票は1人1回。{pollAnonymous?'投票者のPoker IDは公開されません。':'投票者の名前・Poker IDと投票先が公開されます。'} 投稿後の投票方式は変更できません。</p>
    {error && <p role="alert" style={{color:'#ff9999'}}>{error}</p>}
    <button type="button" onClick={submit} disabled={busy||!content.trim()||options.some(o=>!o.trim())} style={{width:'auto',borderRadius:24,background:'#343b45',color:'#fff',border:'1px solid #69717d',padding:'10px 20px',fontWeight:700}}>{busy?'投稿中…':'アンケートを投稿'}</button>
  </section>
}

export function InteractiveCard({item,result,onUpdated,isOwner=false,ownerName: _ownerName='募集者'}:{item:InteractiveItem;result:InteractiveResult|undefined;onUpdated:()=>Promise<void>;isOwner?:boolean;ownerName?:string}) {
  const [choice,setChoice]=useState<number|null>(null)
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const [voterOption,setVoterOption]=useState<number|null>(null)
  const mine=result?.has_responded ?? false

  const closed=item.kind==='poll'&&!!item.closes_at&&Date.parse(item.closes_at)<=Date.now()
  const submit=async()=>{
    if(busy||mine||closed||choice===null) return
    setBusy(true);setError('')
    try {
      const {error:failure}=await supabase.rpc('submit_interactive_response_v2',pollVoteRequest(item, choice))
      if(failure) throw failure
      await onUpdated()
    } catch(e){setError(e instanceof Error?e.message:'回答に失敗しました')}
    finally{setBusy(false)}
  }
  // Historical question code/data is retained, but never mounted publicly.
  if (item.kind !== 'poll') return null
  if (result) result = pollDisplayResult(item.is_anonymous, result)
  return <div style={{margin:'12px 0',padding:14,border:'1px solid #383838',borderRadius:12,color:'#eee'}}>
    <strong style={{fontSize:13}}>{`📊 アンケート（${item.is_anonymous?'匿名':'記名'}）`}</strong>
    <p style={{fontSize:12,color:item.is_anonymous?'#aaa':'#f0ce88',margin:'8px 0'}}>{item.is_anonymous?'投票者の名前は公開されません。':'投票すると、あなたの名前・Poker IDと投票先が全員に公開されます。'}</p>
    <>
      <div style={{display:'grid',gap:8,marginTop:12}}>{item.options.map((option,i)=>{
        const count=result?.vote_counts?.[String(i)] ?? 0
        const show=mine||closed||isOwner
        const pct=result?.total_votes?Math.round(count/result.total_votes*100):0
        return <button key={i} type="button" disabled={busy||(item.is_anonymous&&(mine||closed))} onClick={()=>{if(!item.is_anonymous&&(mine||closed)){setVoterOption(i)}else if(!mine&&!closed){setChoice(i)}}} style={{position:'relative',overflow:'hidden',textAlign:'left',borderRadius:9,padding:12,color:'#fff',border:`1px solid ${choice===i||(mine && result?.my_option_index===i)?'#8b9bad':'#444'}`,background:'#222'}}>
          {show&&<span style={{position:'absolute',inset:0,right:`${100-pct}%`,background:'#405367',transition:'right 240ms ease-out',pointerEvents:'none'}}/>}
          <span style={{position:'relative',zIndex:1,display:'flex',alignItems:'center',justifyContent:'space-between',gap:12,textShadow:'0 1px 2px #151515'}}><span>{String.fromCharCode(65+i)}：{option}</span>{show&&<strong style={{whiteSpace:'nowrap',fontVariantNumeric:'tabular-nums'}}>{pct}%</strong>}</span>
        </button>
      })}</div>
      {voterOption!==null&&!item.is_anonymous&&<div role="dialog" aria-modal="true" aria-label="投票者一覧" style={{position:'fixed',inset:0,zIndex:10000,background:'rgba(0,0,0,.78)',display:'flex',alignItems:'center',justifyContent:'center',padding:16}} onClick={()=>setVoterOption(null)}><div onClick={e=>e.stopPropagation()} style={{background:'#20242b',color:'#fff',border:'1px solid #505b68',borderRadius:14,padding:18,width:'min(100%,460px)',maxHeight:'80vh',overflowY:'auto'}}><div style={{display:'flex',alignItems:'center',justifyContent:'space-between',gap:12,marginBottom:12}}><strong>投票者一覧</strong><button type="button" onClick={()=>setVoterOption(null)} style={{width:'auto',background:'#343b45',color:'#fff',border:'1px solid #667085',borderRadius:8,padding:'6px 12px'}}>閉じる</button></div><div role="tablist" aria-label="選択肢" style={{display:'grid',gridTemplateColumns:'repeat('+item.options.length+',minmax(0,1fr))',gap:6,marginBottom:12}}>{item.options.map((option,i)=><button key={i} type="button" role="tab" aria-label={String.fromCharCode(65+i)+'：'+option} aria-selected={voterOption===i} onClick={()=>setVoterOption(i)} style={{minWidth:0,width:'100%',padding:'9px 4px',borderRadius:8,background:voterOption===i?'#405367':'#292e35',color:'#fff',border:'1px solid '+(voterOption===i?'#8b9bad':'#464d57')}}><strong style={{display:'block'}}>{String.fromCharCode(65+i)}</strong><span style={{fontSize:12}}>{result?.total_votes?Math.round((result?.vote_counts?.[String(i)]??0)/result.total_votes*100):0}%</span></button>)}</div><div style={{padding:'10px 12px',marginBottom:10,background:'#292e35',borderRadius:8,overflowWrap:'anywhere'}}><strong>{String.fromCharCode(65+voterOption)}：{item.options[voterOption]}</strong><div style={{fontSize:12,color:'#b8c2cf',marginTop:4}}>{result?.vote_counts?.[String(voterOption)]??0}票 · {result?.total_votes?Math.round((result?.vote_counts?.[String(voterOption)]??0)/result.total_votes*100):0}%</div></div>{(result?.voters??[]).filter(v=>v.option_index===voterOption).map((v,j)=><div key={j} style={{padding:'10px 2px',borderBottom:'1px solid #373d46'}}><strong>{v.display_name||v.poker_id||'ユーザー'}</strong>{v.poker_id&&<span style={{fontSize:12,color:'#aab5c2'}}> @{v.poker_id}</span>}</div>)}{!(result?.voters??[]).some(v=>v.option_index===voterOption)&&<p style={{fontSize:13,color:'#aaa'}}>まだ投票者はいません。</p>}</div></div>}
      <p style={{fontSize:12,color:'#aaa'}}>{result?.total_votes ?? 0}票 · {closed?'終了':`締切 ${new Date(item.closes_at!).toLocaleString('ja-JP')}`}</p>
      {!mine&&!closed&&<button type="button" disabled={choice===null||busy} onClick={submit} style={{width:'auto',padding:'8px 18px',borderRadius:20,background:'#303b49',color:'#eee',border:'1px solid #64748b'}}>投票する</button>}
      {isOwner&&!item.is_anonymous&&<div style={{marginTop:8,display:'flex',flexDirection:'column',alignItems:'flex-start',gap:6}}><button type="button" onClick={()=>setVoterOption(0)} style={{width:'auto',background:'#303b49',color:'#fff',border:'1px solid #64748b',borderRadius:9,padding:'8px 14px'}}>回答者一覧を見る</button><span style={{fontSize:12,color:'#aaa'}}>投稿主も投票できます。投票後は選択肢を押すと回答者一覧が開きます。</span></div>}
      {mine&&<p style={{fontSize:12,color:'#aaa'}}>投票済み（変更不可）{!item.is_anonymous?' · 選択肢を押すと投票者一覧を表示':''}</p>}
    </>
    {error&&<p role="alert" style={{color:'#ff9999'}}>{error}</p>}
  </div>
}

