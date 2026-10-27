import { withVideoRecoveryDeadline } from './videoRecoveryDeadline'
import { supabase } from './supabase'
import { VIDEO_FINALIZE_ROUTE } from './videoApi'

// Review-only. Neither build configuration nor a stored journal enables this.
export const VIDEO_RECOVERY_CANDIDATE_ENABLED = false as boolean

async function requestRecovery(body: Record<string,unknown>,signal?:AbortSignal):Promise<Record<string,unknown>> {
  if(!VIDEO_RECOVERY_CANDIDATE_ENABLED) throw new Error('動画の自動復旧は安全確認待ちです。')
  return withVideoRecoveryDeadline(signal,async requestSignal=>{
  const {data:{session},error}=await supabase.auth.getSession()
  requestSignal.throwIfAborted()
  if(error||!session?.access_token) throw new Error('ログイン情報を確認してください。')
  const response=await fetch(VIDEO_FINALIZE_ROUTE,{method:'POST',cache:'no-store',redirect:'error',
    headers:{Authorization:'Bearer '+session.access_token,'Content-Type':'application/json'},body:JSON.stringify(body),
    signal:requestSignal})
  if(!response.ok) throw new Error('動画の復旧状態を確認できません。安全のため停止しています。')
  const data:unknown=await response.json()
  if(!data||typeof data!=='object'||Array.isArray(data)) throw new Error('復旧応答を確認できません。')
  requestSignal.throwIfAborted()
  return data as Record<string,unknown>
  })
}

/** Call between confirmed reservation and upload in a future approved flow.
 * The hash is a pre-upload commitment, never a trusted ffprobe claim. */
export async function bindVideoRecoveryCandidate(path:string,file:File,content:string,signal?:AbortSignal) {
  if(!VIDEO_RECOVERY_CANDIDATE_ENABLED) throw new Error('動画の自動復旧は安全確認待ちです。')
  if(file.size<1||file.size>20*1024*1024||!['video/mp4','video/webm'].includes(file.type)) throw new Error('動画を確認してください。')
  const sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await file.arrayBuffer()))).map(n=>n.toString(16).padStart(2,'0')).join('')
  const result=await requestRecovery({action:'bind_recovery',object_path:path,sha256,size:file.size,type:file.type,content},signal)
  if(result.bound!==true||!Number.isSafeInteger(result.expires)) throw new Error('復旧予約を確認できません。')
  return result
}

/** Advisory only: never clears a journal, uploads or publishes automatically. */
export async function inspectVideoRecoveryCandidate(path:string,signal?:AbortSignal) {
  const result=await requestRecovery({action:'recovery_status',object_path:path},signal)
  if(result.allow_resume!==false||!['waiting_for_upload','verified_ready','published'].includes(String(result.state))) throw new Error('復旧応答を確認できません。')
  return result
}

/** Still disabled. A future approved UI must authenticate the owner and preserve
 * its immutable content; server re-probes and DB atomically rechecks manifest. */
export async function finalizeRecoveredVideoCandidate(path:string,content:string,signal?:AbortSignal):Promise<string> {
  const result=await requestRecovery({action:'recovery_finalize',object_path:path,content},signal)
  if(result.state!=='published'||typeof result.post_id!=='string'||!/^[0-9a-f-]{36}$/.test(result.post_id)) throw new Error('動画の復旧確定を確認できません。')
  return result.post_id
}
