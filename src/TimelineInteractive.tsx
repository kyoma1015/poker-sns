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
      const { error: failure } = await supabase.rpc('create_interactive_post_v4', {
        p_content: content.trim(), p_kind: kind,
        p_options: options.map(s => s.trim()),
        p_hours: hours,
        p_is_anonymous: pollAnonymous,
        p_question_policy: null,
      })
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
      <div style={{display:'grid',gap:8,marginTop:10}}>{options.map((v,i)=><input key={i} aria-label={`選択肢${i+1}`} maxLength={80} placeholder={`選択肢${i+1}`} value={v} onChange={e=>setOptions(a=>a.map((s,j)=>j===i?e.target.value:s))} style={inputStyle}/>)}</div>
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

export function InteractiveCard({item,result,onUpdated,isOwner=false,ownerName='募集者'}:{item:InteractiveItem;result:InteractiveResult|undefined;onUpdated:()=>Promise<void>;isOwner?:boolean;ownerName?:string}) {
  const [choice,setChoice]=useState<number|null>(null)
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const [voterOption,setVoterOption]=useState<number|null>(null)
  const mine=result?.has_responded ?? false
  const questionPolicy=item.question_response_policy??(item.is_anonymous?'anonymous_only':'named_only')
  const closed=item.kind==='poll'&&!!item.closes_at&&Date.parse(item.closes_at)<=Date.now()
  const submit=async()=>{
    if(busy||mine) return
    setBusy(true);setError('')
    try {
      const {error:failure}=await supabase.rpc('submit_interactive_response_v2',{p_post_id:item.post_id,p_option_index:item.kind==='poll'?choice:null,p_answer:null,p_is_anonymous:true})
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
        const show=mine||closed||isOwner
        const pct=result?.total_votes?Math.round(count/result.total_votes*100):0
        return <button key={i} type="button" disabled={busy||(item.is_anonymous&&(mine||closed))} onClick={()=>{if(!item.is_anonymous&&(isOwner||mine||closed)){setVoterOption(i)}else if(!mine&&!closed&&!isOwner){setChoice(i)}}} style={{position:'relative',overflow:'hidden',textAlign:'left',borderRadius:9,padding:12,color:'#fff',border:`1px solid ${choice===i||(mine && result?.my_option_index===i)?'#8b9bad':'#444'}`,background:'#222'}}>
          {show&&<span style={{position:'absolute',inset:0,right:`${100-pct}%`,background:'#405367',transition:'right 240ms ease-out',pointerEvents:'none'}}/>}
          <span style={{position:'relative',zIndex:1,display:'flex',alignItems:'center',justifyContent:'space-between',gap:12,textShadow:'0 1px 2px #151515'}}><span>{option}</span>{show&&<strong style={{whiteSpace:'nowrap',fontVariantNumeric:'tabular-nums'}}>{pct}%</strong>}</span>
        </button>
      })}</div>
      {voterOption!==null&&!item.is_anonymous&&<div role="dialog" aria-modal="true" aria-label="投票者一覧" style={{position:'fixed',inset:0,zIndex:10000,background:'rgba(0,0,0,.78)',display:'flex',alignItems:'center',justifyContent:'center',padding:16}} onClick={()=>setVoterOption(null)}><div onClick={e=>e.stopPropagation()} style={{background:'#20242b',color:'#fff',border:'1px solid #505b68',borderRadius:14,padding:18,width:'min(100%,460px)',maxHeight:'80vh',overflowY:'auto'}}><div style={{display:'flex',alignItems:'center',justifyContent:'space-between',gap:12,marginBottom:12}}><strong>{item.options[voterOption]} を選んだ人（{result?.vote_counts?.[String(voterOption)]??0}票）</strong><button type="button" onClick={()=>setVoterOption(null)} style={{width:'auto',background:'#343b45',color:'#fff',border:'1px solid #667085',borderRadius:8,padding:'6px 12px'}}>閉じる</button></div>{(result?.voters??[]).filter(v=>v.option_index===voterOption).map((v,j)=><div key={j} style={{padding:'10px 2px',borderBottom:'1px solid #373d46'}}><strong>{v.display_name||v.poker_id||'ユーザー'}</strong>{v.poker_id&&<span style={{fontSize:12,color:'#aab5c2'}}> @{v.poker_id}</span>}</div>)}{!(result?.voters??[]).some(v=>v.option_index===voterOption)&&<p style={{fontSize:13,color:'#aaa'}}>まだ投票者はいません。</p>}</div></div>}
      <p style={{fontSize:12,color:'#aaa'}}>{result?.total_votes ?? 0}票 · {closed?'終了':`締切 ${new Date(item.closes_at!).toLocaleString('ja-JP')}`}</p>
      {!mine&&!closed&&!isOwner&&<button type="button" disabled={choice===null||busy} onClick={submit} style={{width:'auto',padding:'8px 18px',borderRadius:20,background:'#303b49',color:'#eee',border:'1px solid #64748b'}}>投票する</button>}
      {mine&&<p style={{fontSize:12,color:'#aaa'}}>投票済み（変更不可）{!item.is_anonymous?' · 選択肢を押すと投票者一覧を表示':''}</p>}
    </>:<QuestionThread postId={item.post_id} policy={questionPolicy} onUpdated={onUpdated} isOwner={isOwner} ownerName={ownerName}/> }
    {error&&<p role="alert" style={{color:'#ff9999'}}>{error}</p>}
  </div>
}

type ThreadMessage={id:string;post_id:string;parent_id:string|null;content:string;is_anonymous:boolean;display_name:string|null;poker_id:string|null;created_at:string;is_owner:boolean;is_mine:boolean;edited_at:string|null}
function QuestionThread({postId,policy,onUpdated,isOwner,ownerName}:{postId:string;policy:string;onUpdated:()=>Promise<void>;isOwner:boolean;ownerName:string}) {
 const [messages,setMessages]=useState<ThreadMessage[]>([])
 const [text,setText]=useState('')
 const [anonymous,setAnonymous]=useState(true)
 const [replyTo,setReplyTo]=useState<string|null>(null)
 const [editingId,setEditingId]=useState<string|null>(null)
 const [editText,setEditText]=useState('')
 const [expanded,setExpanded]=useState(false)
 const [visibleCount,setVisibleCount]=useState(10)
 const [filter,setFilter]=useState<'new'|'unanswered'|'answered'>('new')
 const [busy,setBusy]=useState(false)
 const [error,setError]=useState('')
 const refresh=async()=>{const {data,error}=await supabase.rpc('get_question_thread_messages',{p_post_ids:[postId]});if(error)throw error;setMessages((data??[]) as ThreadMessage[])}
 useEffect(()=>{void refresh().catch(e=>setError(e instanceof Error?e.message:'質問の取得に失敗しました'))},[postId])
 const submit=async()=>{if(busy||!text.trim())return;setBusy(true);setError('');try{const {error:e}=await supabase.rpc('add_question_thread_message',{p_post_id:postId,p_content:text.trim(),p_parent_id:replyTo,p_is_anonymous:anonymous});if(e)throw e;setText('');setReplyTo(null);await refresh();await onUpdated()}catch(e){setError(e instanceof Error?e.message:'送信に失敗しました')}finally{setBusy(false)}}
 const manage=async(id:string,action:'edit'|'delete',content?:string)=>{if(busy)return;if(action==='delete'&&!window.confirm('削除しますか？質問を削除すると返信も削除されます。'))return;setBusy(true);setError('');try{const {error:e}=await supabase.rpc('manage_question_thread_message',{p_message_id:id,p_action:action,p_content:content??null});if(e)throw e;setEditingId(null);if(replyTo===id)setReplyTo(null);await refresh();await onUpdated()}catch(e){setError(e instanceof Error?e.message:'操作に失敗しました')}finally{setBusy(false)}}
 const roots=messages.filter(m=>!m.parent_id)
 const children=(id:string)=>messages.filter(m=>m.parent_id===id)
 const answered=(m:ThreadMessage)=>children(m.id).some(r=>r.is_owner)
 const sorted=[...roots].filter(m=>!expanded||filter==='new'||(filter==='answered'?answered(m):!answered(m))).sort((a,b)=>filter==='unanswered'?(Number(answered(a))-Number(answered(b))||Date.parse(b.created_at)-Date.parse(a.created_at)):Date.parse(b.created_at)-Date.parse(a.created_at))
 const visible=expanded?sorted.slice(0,visibleCount):sorted.slice(0,2)
 const selectReply=(m:ThreadMessage)=>{setReplyTo(prev=>prev===m.id?null:m.id);setText('');setAnonymous(m.is_anonymous)}
 const darkButton={width:'auto' as const,padding:'7px 12px',borderRadius:8,background:'#30343b',color:'#eee',border:'1px solid #555'}
 const replyEditor=()=><div style={{marginTop:8,padding:10,background:'#1a1a1a',border:'1px solid #505050',borderRadius:8}}>
 <div style={{fontSize:12,color:'#ccc',marginBottom:7}}>{isOwner?'この質問に回答':'この質問に返信'}</div>
 <textarea aria-label="質問への返信" value={text} maxLength={500} onChange={e=>setText(e.target.value)} placeholder="返信を入力…" style={{width:'100%',boxSizing:'border-box',padding:9,background:'#171717',color:'#fff',border:'1px solid #555',borderRadius:7}}/>
 <div style={{display:'flex',gap:8,marginTop:8}}><button type="button" disabled={busy||!text.trim()} onClick={submit} style={darkButton}>{busy?'送信中…':isOwner?'回答を送信':'返信する'}</button><button type="button" onClick={()=>{setReplyTo(null);setText('')}} style={darkButton}>キャンセル</button></div></div>
 return <div style={{display:'grid',gap:10,marginTop:12}}>
 <p style={{fontSize:12,color:'#aaa',margin:0}}>{roots.length}件の質問 · 回答済み {roots.filter(answered).length}件 · {isOwner?'質問を選んで回答できます':'何回でも質問できます'}</p>
 {expanded&&<div style={{display:'flex',gap:6,flexWrap:'wrap'}}>{([{value:'new',label:'新着順'},{value:'unanswered',label:'未回答'},{value:'answered',label:'回答済み'}] as const).map(f=><button type="button" key={f.value} onClick={()=>{setFilter(f.value);setVisibleCount(10)}} style={{width:'auto',fontSize:12,padding:'6px 10px',background:filter===f.value?'#555':'#222',color:'#fff',borderRadius:8}}>{f.label}</button>)}</div>}
 {visible.map(m=>{const replies=children(m.id);const hasOwnerReply=replies.some(r=>r.is_owner);return <div key={m.id} style={{padding:12,borderRadius:10,background:replyTo===m.id?'#30343b':'#222',border:replyTo===m.id?'1px solid #9ca3af':'1px solid #393939',overflowWrap:'anywhere'}}>
 <div style={{display:'flex',gap:8,alignItems:'center',flexWrap:'wrap'}}><strong style={{fontSize:12}}>{m.is_anonymous?'匿名の質問者':m.display_name||m.poker_id||'ユーザー'}</strong>{!m.is_anonymous&&m.poker_id&&<span style={{fontSize:11,color:'#aaa'}}>@{m.poker_id}</span>}<span style={{fontSize:11,color:hasOwnerReply?'#b7e6bb':'#aaa'}}>{hasOwnerReply?'✓ 回答済み':'未回答'}</span></div>
 <p style={{whiteSpace:'pre-wrap',margin:'8px 0'}}>{m.content}</p>
 {(isOwner||m.is_mine)&&<button type="button" disabled={busy} onClick={()=>void manage(m.id,'delete')} style={{width:'auto',fontSize:11,padding:'5px 9px',background:'#292929',color:'#ddd',border:'1px solid #555',borderRadius:7}}>質問を削除</button>}
 {(expanded?replies:replies.slice(-1)).map(r=><div key={r.id} style={{borderLeft:'2px solid #666',padding:'7px 10px',marginTop:8,background:'#292929',borderRadius:5}}><strong style={{fontSize:12}}>{r.is_owner?`${ownerName}（募集者）からの回答`:r.is_anonymous?'匿名の質問者からの返信':`${r.display_name||r.poker_id||'ユーザー'}からの返信`}</strong>{!r.is_anonymous&&r.poker_id&&<span style={{fontSize:11,color:'#aaa'}}> @{r.poker_id}</span>}{editingId===r.id?<div style={{display:'grid',gap:6,marginTop:6}}><textarea aria-label="回答を編集" maxLength={500} value={editText} onChange={e=>setEditText(e.target.value)} style={{width:'100%',boxSizing:'border-box',background:'#181818',color:'#fff',border:'1px solid #666',borderRadius:7,padding:8}}/><div style={{display:'flex',gap:8}}><button type="button" disabled={busy||!editText.trim()} onClick={()=>void manage(r.id,'edit',editText)} style={darkButton}>保存</button><button type="button" onClick={()=>setEditingId(null)} style={darkButton}>キャンセル</button></div></div>:<p style={{margin:'5px 0',whiteSpace:'pre-wrap'}}>{r.content}{r.edited_at&&<span style={{fontSize:11,color:'#aaa'}}> （編集済み）</span>}</p>}{r.is_mine&&editingId!==r.id&&<div style={{display:'flex',gap:8}}><button type="button" onClick={()=>{setEditingId(r.id);setEditText(r.content)}} style={{width:'auto',fontSize:11,padding:'4px 8px',background:'#333',color:'#ddd'}}>編集</button><button type="button" disabled={busy} onClick={()=>void manage(r.id,'delete')} style={{width:'auto',fontSize:11,padding:'4px 8px',background:'#333',color:'#ddd'}}>削除</button></div>}</div>)}
 {(isOwner||m.is_mine)&&<button type="button" onClick={()=>selectReply(m)} style={{width:'auto',fontSize:12,marginTop:8,padding:'6px 12px',borderRadius:8,background:replyTo===m.id?'#414751':'#292929',color:'#eee',border:'1px solid #555'}}>{replyTo===m.id?'閉じる':isOwner?'回答する':'返信する'}</button>}
 {replyTo===m.id&&replyEditor()}
 </div>})}
 {roots.length>2&&<button type="button" onClick={()=>{setExpanded(!expanded);setVisibleCount(10);setFilter('new')}} style={{width:'100%',padding:10,borderRadius:8,background:'#292929',color:'#fff'}}>{expanded?'閉じる':`すべての質問を見る（${roots.length}件）`}</button>}
 {expanded&&sorted.length>visibleCount&&<button type="button" onClick={()=>setVisibleCount(n=>n+10)} style={{width:'100%',padding:9,background:'#30343b',color:'#eee',border:'1px solid #555',borderRadius:8}}>さらに10件表示</button>}
 {!isOwner&&<div style={{padding:10,border:'1px solid #444',borderRadius:9}}>
 <strong style={{fontSize:13}}>{ownerName}さんに質問する</strong>
 <textarea aria-label="質問を入力" value={replyTo? '':text} maxLength={500} disabled={replyTo!==null} onChange={e=>setText(e.target.value)} placeholder="質問を入力…" style={{display:'block',boxSizing:'border-box',width:'100%',marginTop:8,padding:10,background:'#171717',color:'#fff',border:'1px solid #555',borderRadius:8}}/>
 {policy==='respondent_choice'&&<div style={{display:'flex',gap:8,marginTop:8}}>{([{value:true,label:'匿名で質問'},{value:false,label:'記名で質問'}] as const).map(x=><button key={x.label} type="button" aria-pressed={anonymous===x.value} disabled={replyTo!==null} onClick={()=>setAnonymous(x.value)} style={{...darkButton,background:anonymous===x.value?'#414751':'#292929'}}>{x.label}</button>)}</div>}
 <p style={{fontSize:11,color:'#aaa'}}>{policy==='named_only'?'名前とPoker IDが公開されます。':policy==='anonymous_only'||anonymous?'名前とPoker IDは公開されません。':'名前とPoker IDが公開されます。'} 送信後は変更できません。</p>
 <button type="button" disabled={busy||!text.trim()||replyTo!==null} onClick={submit} style={darkButton}>{busy?'送信中…':'質問する'}</button>
 </div>}
 {error&&<p role="alert" style={{color:'#ff9999'}}>{error}</p>}
 </div>
}
