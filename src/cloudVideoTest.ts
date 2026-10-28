import { supabase } from './supabase'
import { assertCurrentVideoCloudTestClient } from './videoCloudTestGuard'
import { uploadPostVideo, validateVideo } from './videoUpload'
import { finalizeUploadedVideo, loadAuthorizedVideo, recoverCloudVideo } from './videoApi'
import { hasVideoTransferJournal,readVideoTransferHint,finishRecoveredVideoTransfer } from './videoTransferJournal'
assertCurrentVideoCloudTestClient()
const el = (id: string) => document.getElementById(id)!
const status = (message: string) => { el('status').textContent = message }
const state = async () => {
 const {data:{user}} = await supabase.auth.getUser()
 el('auth').hidden = !!user; el('composer').hidden = !user
 el('identity').textContent = user ? 'ログイン中: '+user.email : ''
 if(user) await refresh()
 await updateRecovery()
}
async function refresh() {
 const target=el('posts');target.replaceChildren()
 const {data,error}=await supabase.from('posts').select('id,content,created_at').order('created_at',{ascending:false}).limit(30)
 if(error){status('投稿取得エラー: '+error.message);return}
 for(const post of data||[]){
  const card=document.createElement('article'), p=document.createElement('p'), button=document.createElement('button')
  p.textContent=post.content || '動画';button.textContent='再生'
  card.append(p,button);target.append(card)
  button.onclick=async()=>{
   button.disabled=true
   try{
    const src=await loadAuthorizedVideo(post.id)
    const player=document.createElement('video');player.controls=true;player.playsInline=true;player.src=src
    player.addEventListener('error',()=>URL.revokeObjectURL(src),{once:true})
    card.append(player);await player.play().catch(()=>{})
   }catch(e){status('動画再生に失敗: '+String(e))}
   finally{button.disabled=false}
  }
 }
}
// Recover only the exact prior reservation; never upload bytes or create a replacement key.
const recoverButton=document.createElement('button')
recoverButton.textContent='前回の送信を安全に再確認'
recoverButton.hidden=true
el('post').parentElement?.append(recoverButton)
const updateRecovery=async()=>{
 const {data:{user}}=await supabase.auth.getUser()
 recoverButton.hidden=!user||!hasVideoTransferJournal(user.id)
}
recoverButton.onclick=async()=>{
 recoverButton.disabled=true
 try{
  const {data:{user},error}=await supabase.auth.getUser()
  if(error||!user)throw Error('ログインしてください')
  const hint=readVideoTransferHint(user.id)
  status('前回保存した動画を再検証中…新しいアップロードはしません。')
  await recoverCloudVideo(hint.path)
  finishRecoveredVideoTransfer(user.id,hint.path,hint.raw)
  status('前回の動画を投稿として確定しました')
  await refresh()
 }catch(e){status('復旧に失敗: '+String(e))}
 finally{recoverButton.disabled=false;await updateRecovery()}
}
el('login').onclick=async()=>{
 const {error}=await supabase.auth.signInWithPassword({email:(el('email') as HTMLInputElement).value,password:(el('password') as HTMLInputElement).value})
 status(error?error.message:'ログインしました');if(!error)await state()
}
el('signup').onclick=async()=>{
 const {error}=await supabase.auth.signUp({email:(el('email') as HTMLInputElement).value,password:(el('password') as HTMLInputElement).value})
 status(error?error.message:'登録申請しました。確認メールが届く場合は認証してください。許可ユーザー登録が必要です。');if(!error)await state()
}
el('logout').onclick=async()=>{await supabase.auth.signOut();await state()}
el('post').onclick=async()=>{
 const button=el('post') as HTMLButtonElement;button.disabled=true
 try{
  const file=(el('video') as HTMLInputElement).files?.[0],content=(el('content') as HTMLTextAreaElement).value
  if(!file)throw Error('動画ファイルを選択してください')
  const err=await validateVideo(file);if(err)throw Error(err)
  const {data:{user},error}=await supabase.auth.getUser()
  if(error||!user)throw Error('ログインしてください')
  status('予約・アップロード中…')
  const path=await uploadPostVideo(user.id,file,undefined,content)
  status('動画を検証・確定中…')
  await finalizeUploadedVideo(path,content)
  status('投稿が完了しました');await refresh()
 }catch(e){status('投稿に失敗: '+String(e))}finally{button.disabled=false;await updateRecovery()}
}
supabase.auth.onAuthStateChange(()=>{void state()});void state()