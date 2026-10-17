import { useState } from 'react'
import { supabase } from './supabase'

export type InteractiveItem = {
  post_id: string
  kind: 'poll' | 'question'
  options: string[]
  closes_at: string | null
  is_anonymous: boolean
}
export type InteractiveResult = { post_id: string; total_votes: number; vote_counts: Record<string,number>; answers: {answer:string;poker_id?:string;display_name?:string;avatar_url?:string}[]; my_option_index: number | null; has_responded: boolean; voters: {option_index:number;poker_id?:string;display_name?:string;avatar_url?:string}[] }

export function InteractiveComposer({ onCreated }: { onCreated: () => Promise<void> }) {
  const [kind, setKind] = useState<'poll'|'question'>('poll')
  const [content, setContent] = useState('')
  const [options, setOptions] = useState(['',''])
  const [hours, setHours] = useState(24)
  const [questionAnonymous, setQuestionAnonymous] = useState(true)
  const [pollAnonymous, setPollAnonymous] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const submit = async () => {
    if (busy) return
    setBusy(true); setError('')
    try {
      const { error: failure } = await supabase.rpc('create_interactive_post_v3', {
        p_content: content.trim(), p_kind: kind,
        p_options: kind === 'poll' ? options.map(s => s.trim()) : null,
        p_hours: hours,
        p_is_anonymous: kind==='poll'?pollAnonymous:questionAnonymous,
      })
      if (failure) throw failure
      setContent(''); setOptions(['',''])
      await onCreated()
    } catch (e) { setError(e instanceof Error ? e.message : '投稿に失敗しました') }
    finally { setBusy(false) }
  }
  const inputStyle = { width:'100%', boxSizing:'border-box' as const, padding:10, borderRadius:8, background:'#202020', color:'#fff', border:'1px solid #444' }
  return <section style={{padding:16,border:'1px solid #333',borderRadius:12,marginBottom:16,color:'#fff'}}>
    <div style={{display:'flex',gap:8,marginBottom:12}}>
      {(['poll','question'] as const).map(k=><button key={k} type="button" onClick={()=>setKind(k)} style={{width:'auto',background:kind===k?'#fff':'#292929',color:kind===k?'#111':'#fff',padding:'8px 14px',borderRadius:9}}>{k==='poll'?'📊 アンケート':'💬 質問箱'}</button>)}
    </div>
    <textarea aria-label="質問内容" value={content} onChange={e=>setContent(e.target.value)} maxLength={500} placeholder={kind==='poll'?'みんなに聞きたいことは？':'みんなから回答を募集する質問は？'} style={{...inputStyle,minHeight:72}} />
    {kind==='poll' && <>
      <div style={{display:'grid',gap:8,marginTop:10}}>{options.map((v,i)=><input key={i} aria-label={`選択肢${i+1}`} maxLength={80} placeholder={`選択肢${i+1}`} value={v} onChange={e=>setOptions(a=>a.map((s,j)=>j===i?e.target.value:s))} style={inputStyle}/>)}</div>
      <div style={{display:'flex',gap:8,alignItems:'center',marginTop:10}}>
        {options.length<4 && <button type="button" onClick={()=>setOptions(a=>[...a,''])} style={{width:'auto'}}>＋ 選択肢</button>}
        {options.length>2 && <button type="button" onClick={()=>setOptions(a=>a.slice(0,-1))} style={{width:'auto'}}>− 削除</button>}
        <label style={{fontSize:13}}>投票期限 <select value={hours} onChange={e=>setHours(Number(e.target.value))} style={{background:'#222',color:'#fff',padding:6}}>{[1,6,24,72,168].map(h=><option key={h} value={h}>{h<24?`${h}時間`:`${h/24}日`}</option>)}</select></label>
      </div>
      <div style={{display:'flex',gap:8,marginTop:10}}>{([{anonymous:true,label:'匿名投票'},{anonymous:false,label:'記名投票'}] as const).map(mode=><button key={mode.label} type="button" aria-pressed={pollAnonymous===mode.anonymous} onClick={()=>setPollAnonymous(mode.anonymous)} style={{width:'auto',background:pollAnonymous===mode.anonymous?'#393939':'#181818',color:'#eee',border:'1px solid '+(pollAnonymous===mode.anonymous?'#ddd':'#444'),padding:'8px 12px',borderRadius:9}}>{mode.label}</button>)}</div>
    </>}
    {kind==='question'&&<div style={{display:'flex',gap:8,marginTop:10}}>{([{anonymous:true,label:'匿名で回答'},{anonymous:false,label:'名前を表示'}] as const).map(mode=><button key={mode.label} type="button" aria-pressed={questionAnonymous===mode.anonymous} onClick={()=>setQuestionAnonymous(mode.anonymous)} style={{width:'auto',background:questionAnonymous===mode.anonymous?'#393939':'#181818',color:'#eee',border:'1px solid '+(questionAnonymous===mode.anonymous?'#ddd':'#444'),padding:'8px 12px',borderRadius:9}}>{mode.label}</button>)}</div>}
    <p style={{fontSize:12,color:'#aaa'}}>投票・回答は1人1回。{kind==='poll'?(pollAnonymous?'投票者のPoker IDは公開されません。':'投票者の名前・Poker IDと投票先が公開されます。'):questionAnonymous?'回答者の名前は公開されません。':'回答者のプロフィール情報が公開されます。'} 投稿後の回答方式は変更できません。</p>
    {error && <p role="alert" style={{color:'#ff9999'}}>{error}</p>}
    <button type="button" onClick={submit} disabled={busy||!content.trim()||(kind==='poll'&&options.some(o=>!o.trim()))} style={{width:'auto',borderRadius:24,background:'#fff',color:'#111',padding:'10px 20px',fontWeight:700}}>{busy?'投稿中…':kind==='poll'?'アンケートを投稿':'質問を投稿'}</button>
  </section>
}

export function InteractiveCard({item,result,onUpdated}:{item:InteractiveItem;result:InteractiveResult|undefined;onUpdated:()=>Promise<void>}) {
  const [choice,setChoice]=useState<number|null>(null)
  const [answer,setAnswer]=useState('')
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const mine=result?.has_responded ?? false
  const closed=item.kind==='poll'&&!!item.closes_at&&Date.parse(item.closes_at)<=Date.now()
  const submit=async()=>{
    if(busy||mine) return
    setBusy(true);setError('')
    try {
      const {error:failure}=await supabase.rpc('submit_interactive_response',{p_post_id:item.post_id,p_option_index:item.kind==='poll'?choice:null,p_answer:item.kind==='question'?answer.trim():null})
      if(failure) throw failure
      await onUpdated()
    } catch(e){setError(e instanceof Error?e.message:'回答に失敗しました')}
    finally{setBusy(false)}
  }
  return <div style={{margin:'12px 0',padding:14,border:'1px solid #383838',borderRadius:12,color:'#eee'}}>
    <strong style={{fontSize:13}}>{item.kind==='poll'?`📊 アンケート（${item.is_anonymous?'匿名':'記名'}）`:`💬 質問箱（${item.is_anonymous?'匿名':'記名'}）`}</strong>
    <p style={{fontSize:12,color:item.is_anonymous?'#aaa':'#f0ce88',margin:'8px 0'}}>{item.is_anonymous?'回答者の名前は公開されません。':item.kind==='poll'?'投票すると、あなたの名前・Poker IDと投票先が全員に公開されます。':'回答すると、あなたの名前・Poker IDが全員に公開されます。'}</p>
    {item.kind==='poll'?<>
      <div style={{display:'grid',gap:8,marginTop:12}}>{item.options.map((option,i)=>{
        const count=result?.vote_counts?.[String(i)] ?? 0
        const show=mine||closed
        const pct=result?.total_votes?Math.round(count/result.total_votes*100):0
        return <button key={i} type="button" disabled={mine||closed||busy} onClick={()=>setChoice(i)} style={{position:'relative',overflow:'hidden',textAlign:'left',borderRadius:9,padding:12,color:'#fff',border:`1px solid ${choice===i||(mine && result?.my_option_index===i)?'#fff':'#444'}`,background:'#222'}}>
          {show&&<span style={{position:'absolute',inset:0,right:`${100-pct}%`,background:'#414141'}}/>}
          <span style={{position:'relative'}}>{option}{show?` — ${pct}%`:''}</span>
        </button>
      })}</div>
      {!item.is_anonymous&&(result?.voters?.length??0)>0&&<div style={{display:'grid',gap:6,marginTop:10}}>{item.options.map((option,i)=>{const voters=(result?.voters??[]).filter(v=>v.option_index===i);return voters.length>0?<div key={i} style={{background:'#1b1b1b',padding:10,borderRadius:8}}><strong style={{fontSize:12}}>{option}</strong><div style={{display:'flex',gap:8,flexWrap:'wrap',marginTop:6}}>{voters.map((v,j)=><span key={j} style={{fontSize:12,color:'#ddd'}}>{v.display_name||v.poker_id||'ユーザー'}{v.poker_id?' (@'+v.poker_id+')':''}</span>)}</div></div>:null})}</div>}
      <p style={{fontSize:12,color:'#aaa'}}>{result?.total_votes ?? 0}票 · {closed?'終了':`締切 ${new Date(item.closes_at!).toLocaleString('ja-JP')}`}</p>
      {!mine&&!closed&&<button type="button" disabled={choice===null||busy} onClick={submit} style={{width:'auto',padding:'8px 18px',borderRadius:20}}>投票する</button>}
      {mine&&<p style={{fontSize:12,color:'#aaa'}}>投票済み（変更不可）</p>}
    </>:<>
      <div style={{marginTop:12,display:'grid',gap:8}}>{(result?.answers ?? []).map((r,i)=><p key={i} style={{background:'#222',padding:10,borderRadius:8,margin:0,overflowWrap:'anywhere'}}><span style={{color:'#aaa',fontSize:11}}>{item.is_anonymous?'匿名回答':r.display_name||r.poker_id||'ユーザー'} {!item.is_anonymous&&r.poker_id?'(@'+r.poker_id+')':''}</span>　{r.answer}</p>)}</div>
      <p style={{fontSize:12,color:'#aaa'}}>{result?.answers?.length ?? 0}件の回答</p>
      {!mine&&<><textarea aria-label="質問への回答" value={answer} onChange={e=>setAnswer(e.target.value)} maxLength={500} placeholder={item.is_anonymous?"匿名で回答を入力…":"名前を公開して回答を入力…"} style={{width:'100%',boxSizing:'border-box',background:'#222',color:'#fff',border:'1px solid #444',borderRadius:8,padding:10}}/><button type="button" disabled={!answer.trim()||busy} onClick={submit} style={{width:'auto',padding:'8px 18px',borderRadius:20}}>回答する</button></>}
      {mine&&<p style={{fontSize:12,color:'#aaa'}}>回答済み（変更不可）</p>}
    </>}
    {error&&<p role="alert" style={{color:'#ff9999'}}>{error}</p>}
  </div>
}
