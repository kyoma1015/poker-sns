import { useEffect, useState } from 'react'
import { supabase } from './supabase'

export type InteractiveItem = {
  post_id: string
  kind: 'poll' | 'question'
  options: string[]
  closes_at: string | null
  is_anonymous: boolean
  question_response_policy?: 'anonymous_only'|'named_only'|'respondent_choice'|null
}
export type InteractiveResult = { post_id: string; total_votes: number; vote_counts: Record<string,number>; answers: {answer:string;is_anonymous?:boolean;poker_id?:string;display_name?:string;avatar_url?:string}[]; my_option_index: number | null; has_responded: boolean; voters: {option_index:number;poker_id?:string;display_name?:string;avatar_url?:string}[] }

export function InteractiveComposer({ onCreated }: { onCreated: () => Promise<void> }) {
  const [kind, setKind] = useState<'poll'|'question'>('poll')
  const [content, setContent] = useState('')
  const [options, setOptions] = useState(['',''])
  const [hours, setHours] = useState(24)
  const [questionPolicy, setQuestionPolicy] = useState<'named_only'|'respondent_choice'>('respondent_choice')
  const [pollAnonymous, setPollAnonymous] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const submit = async () => {
    if (busy) return
    setBusy(true); setError('')
    try {
      const { error: failure } = await supabase.rpc('create_interactive_post_v4', {
        p_content: content.trim(), p_kind: kind,
        p_options: kind === 'poll' ? options.map(s => s.trim()) : null,
        p_hours: hours,
        p_is_anonymous: pollAnonymous,
        p_question_policy: kind==='question'?questionPolicy:null,
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
    {kind==='question'&&<div style={{display:'flex',gap:8,marginTop:10}}>{([{policy:'named_only',label:'記名回答のみ'},{policy:'respondent_choice',label:'回答者が選択'}] as const).map(mode=><button key={mode.policy} type="button" aria-pressed={questionPolicy===mode.policy} onClick={()=>setQuestionPolicy(mode.policy)} style={{width:'auto',background:questionPolicy===mode.policy?'#393939':'#181818',color:'#eee',border:'1px solid '+(questionPolicy===mode.policy?'#ddd':'#444'),padding:'8px 12px',borderRadius:9}}>{mode.label}</button>)}</div>}
    <p style={{fontSize:12,color:'#aaa'}}>投票・回答は1人1回。{kind==='poll'?(pollAnonymous?'投票者のPoker IDは公開されません。':'投票者の名前・Poker IDと投票先が公開されます。'):questionPolicy==='named_only'?'記名回答のみです。回答者のプロフィール情報が公開されます。':'回答者が匿名・記名を選択できます。'} 投稿後の回答方式は変更できません。</p>
    {error && <p role="alert" style={{color:'#ff9999'}}>{error}</p>}
    <button type="button" onClick={submit} disabled={busy||!content.trim()||(kind==='poll'&&options.some(o=>!o.trim()))} style={{width:'auto',borderRadius:24,background:'#fff',color:'#111',padding:'10px 20px',fontWeight:700}}>{busy?'投稿中…':kind==='poll'?'アンケートを投稿':'質問を投稿'}</button>
  </section>
}

export function InteractiveCard({item,result,onUpdated}:{item:InteractiveItem;result:InteractiveResult|undefined;onUpdated:()=>Promise<void>}) {
  const [choice,setChoice]=useState<number|null>(null)
  const [answer,setAnswer]=useState('')
  const [respondAnonymously,setRespondAnonymously]=useState(true)
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const mine=result?.has_responded ?? false
  const questionPolicy=item.question_response_policy??(item.is_anonymous?'anonymous_only':'named_only')
  const closed=item.kind==='poll'&&!!item.closes_at&&Date.parse(item.closes_at)<=Date.now()
  const submit=async()=>{
    if(busy||mine) return
    setBusy(true);setError('')
    try {
      const {error:failure}=await supabase.rpc('submit_interactive_response_v2',{p_post_id:item.post_id,p_option_index:item.kind==='poll'?choice:null,p_answer:item.kind==='question'?answer.trim():null,p_is_anonymous:respondAnonymously})
      if(failure) throw failure
      await onUpdated()
    } catch(e){setError(e instanceof Error?e.message:'回答に失敗しました')}
    finally{setBusy(false)}
  }
  return <div style={{margin:'12px 0',padding:14,border:'1px solid #383838',borderRadius:12,color:'#eee'}}>
    <strong style={{fontSize:13}}>{item.kind==='poll'?`📊 アンケート（${item.is_anonymous?'匿名':'記名'}）`:`💬 質問箱（${questionPolicy==='respondent_choice'?'匿名・記名を選択':questionPolicy==='named_only'?'記名回答のみ':'匿名回答のみ'}）`}</strong>
    <p style={{fontSize:12,color:item.is_anonymous?'#aaa':'#f0ce88',margin:'8px 0'}}>{item.kind==='poll'?(item.is_anonymous?'投票者の名前は公開されません。':'投票すると、あなたの名前・Poker IDと投票先が全員に公開されます。'):questionPolicy==='respondent_choice'?'回答時に匿名・記名を選択できます。':questionPolicy==='named_only'?'回答すると、あなたの名前・Poker IDが全員に公開されます。':'回答者の名前は公開されません。'}</p>
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
    </>:<QuestionThread postId={item.post_id} policy={questionPolicy} onUpdated={onUpdated}/> }
    {error&&<p role="alert" style={{color:'#ff9999'}}>{error}</p>}
  </div>
}

type ThreadMessage={id:string;post_id:string;parent_id:string|null;content:string;is_anonymous:boolean;display_name:string|null;poker_id:string|null;created_at:string;is_owner:boolean}
function QuestionThread({postId,policy,onUpdated}:{postId:string;policy:string;onUpdated:()=>Promise<void>}) {
 const [messages,setMessages]=useState<ThreadMessage[]>([])
 const [text,setText]=useState('')
 const [anonymous,setAnonymous]=useState(true)
 const [replyTo,setReplyTo]=useState<string|null>(null)
 const [expanded,setExpanded]=useState(false)
 const [visibleCount,setVisibleCount]=useState(10)
 const [filter,setFilter]=useState<'new'|'unanswered'|'answered'>('new')
 const [busy,setBusy]=useState(false)
 const [error,setError]=useState('')
 const refresh=async()=>{const {data,error}=await supabase.rpc('get_question_thread_messages',{p_post_ids:[postId]});if(error)throw error;setMessages((data??[]) as ThreadMessage[])}
 useEffect(()=>{void refresh().catch(e=>setError(e instanceof Error?e.message:'質問の取得に失敗しました'))},[postId])
 const submit=async()=>{if(busy||!text.trim())return;setBusy(true);setError('');try{const {error:e}=await supabase.rpc('add_question_thread_message',{p_post_id:postId,p_content:text.trim(),p_parent_id:replyTo,p_is_anonymous:anonymous});if(e)throw e;setText('');setReplyTo(null);await refresh();await onUpdated()}catch(e){setError(e instanceof Error?e.message:'送信に失敗しました')}finally{setBusy(false)}}
 const roots=messages.filter(m=>!m.parent_id)
 const children=(id:string)=>messages.filter(m=>m.parent_id===id)
 const answered=(m:ThreadMessage)=>children(m.id).some(r=>r.is_owner)
 const sorted=[...roots].filter(m=>!expanded||filter==='new'||(filter==='answered'?answered(m):!answered(m))).sort((a,b)=>filter==='unanswered'?(Number(answered(a))-Number(answered(b))||Date.parse(b.created_at)-Date.parse(a.created_at)):Date.parse(b.created_at)-Date.parse(a.created_at))
 const visible=expanded?sorted.slice(0,visibleCount):sorted.slice(0,2)
 return <div style={{display:'grid',gap:10,marginTop:12}}>
 <p style={{fontSize:12,color:'#aaa',margin:0}}>{roots.length}件の質問 · 回答済み {roots.filter(answered).length}件 · 何回でも質問できます</p>
 {expanded&&<div style={{display:'flex',gap:6,flexWrap:'wrap'}}>{([{value:'new',label:'新着順'},{value:'unanswered',label:'未回答'},{value:'answered',label:'回答済み'}] as const).map(f=><button type="button" key={f.value} onClick={()=>{setFilter(f.value);setVisibleCount(10)}} style={{width:'auto',fontSize:12,padding:'6px 10px',background:filter===f.value?'#555':'#222',color:'#fff',borderRadius:8}}>{f.label}</button>)}</div>}
 {visible.map(m=>{const replies=children(m.id);const hasOwnerReply=replies.some(r=>r.is_owner);return <div key={m.id} style={{padding:12,borderRadius:10,background:'#222',overflowWrap:'anywhere'}}>
 <div style={{display:'flex',gap:8,alignItems:'center',flexWrap:'wrap'}}><strong style={{fontSize:12}}>{m.is_anonymous?'匿名の質問者':m.display_name||m.poker_id||'ユーザー'}</strong>{!m.is_anonymous&&m.poker_id&&<span style={{fontSize:11,color:'#aaa'}}>@{m.poker_id}</span>}<span style={{fontSize:11,color:hasOwnerReply?'#b7e6bb':'#aaa'}}>{hasOwnerReply?'✓ 回答済み':'未回答'}</span></div>
 <p style={{whiteSpace:'pre-wrap',margin:'8px 0'}}>{m.content}</p>
 {(expanded?replies:replies.slice(-1)).map(r=><div key={r.id} style={{borderLeft:'2px solid #666',padding:'7px 10px',marginTop:8,background:'#292929',borderRadius:5}}><strong style={{fontSize:12}}>{r.is_owner?'募集者':r.is_anonymous?'匿名の質問者':r.display_name||r.poker_id||'ユーザー'}</strong>{!r.is_anonymous&&r.poker_id&&<span style={{fontSize:11,color:'#aaa'}}> @{r.poker_id}</span>}<p style={{margin:'5px 0',whiteSpace:'pre-wrap'}}>{r.content}</p></div>)}
 <button type="button" onClick={()=>{setReplyTo(m.id);setText('');setAnonymous(m.is_anonymous)}} style={{width:'auto',fontSize:12,marginTop:8,padding:'6px 12px',borderRadius:8}}>返信する</button>
 </div>})}
 {roots.length>2&&<button type="button" onClick={()=>{setExpanded(!expanded);setVisibleCount(10);setFilter('new')}} style={{width:'100%',padding:10,borderRadius:8,background:'#292929',color:'#fff'}}>{expanded?'閉じる':`すべての質問を見る（${roots.length}件）`}</button>}
 {expanded&&sorted.length>visibleCount&&<button type="button" onClick={()=>setVisibleCount(n=>n+10)} style={{width:'100%',padding:9}}>さらに10件表示</button>}
 <div style={{padding:10,border:'1px solid #444',borderRadius:9}}>
 <strong style={{fontSize:12}}>{replyTo?'質問に返信':'質問を送る'}</strong>
 {replyTo&&<button type="button" onClick={()=>{setReplyTo(null);setText('')}} style={{width:'auto',marginLeft:8,fontSize:12}}>返信をやめる</button>}
 <textarea aria-label={replyTo?'質問への返信':'質問を入力'} value={text} maxLength={500} onChange={e=>setText(e.target.value)} placeholder={replyTo?'返信を入力…':'質問を入力…'} style={{display:'block',boxSizing:'border-box',width:'100%',marginTop:8,padding:10,background:'#171717',color:'#fff',border:'1px solid #555',borderRadius:8}}/>
 {!replyTo&&policy==='respondent_choice'&&<div style={{display:'flex',gap:8,marginTop:8}}>{([{value:true,label:'匿名で質問'},{value:false,label:'記名で質問'}] as const).map(x=><button key={x.label} type="button" aria-pressed={anonymous===x.value} onClick={()=>setAnonymous(x.value)} style={{width:'auto',padding:'7px 12px',borderRadius:8,background:anonymous===x.value?'#555':'#222',color:'#fff'}}>{x.label}</button>)}</div>}
 <p style={{fontSize:11,color:'#aaa'}}>{replyTo?'返信先の匿名性は維持されます。':policy==='named_only'?'名前とPoker IDが公開されます。':policy==='anonymous_only'||anonymous?'名前とPoker IDは公開されません。':'名前とPoker IDが公開されます。'} 送信後は変更できません。</p>
 <button type="button" disabled={busy||!text.trim()} onClick={submit} style={{width:'auto',padding:'8px 18px',borderRadius:18}}>{busy?'送信中…':replyTo?'返信する':'質問する'}</button>
 </div>
 {error&&<p role="alert" style={{color:'#ff9999'}}>{error}</p>}
 </div>
}
