import { createVideoAttestationNonce, signBinaryVideoAttestation, videoAttestationDigest } from '../server/video-attestation.js'
import { createClient } from '@supabase/supabase-js'
import type { VercelRequest, VercelResponse } from '@vercel/node'
import { inspectStagedVideo } from './video-preflight.js'

const pathPattern=/^([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})\/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\.(mp4|webm)$/
const MAX_BYTES=20*1024*1024

/** Review-only advisory endpoint, sharing finalize's function. No production
 * activation path, no publication/cleanup, no privileged credentials. */
export async function handleVideoRecoveryCandidate(req: VercelRequest,res: VercelResponse,isolated: boolean) {
  const url=process.env.VITE_SUPABASE_URL,anon=process.env.VITE_SUPABASE_ANON_KEY
  if (!isolated || url!=='http://127.0.0.1:56321' || !anon) return res.status(503).json({error:'recovery_not_enabled'})
  const body=req.body as Record<string,unknown>
  const bind=body.action==='bind_recovery'
  const finalize=body.action==='recovery_finalize'
  const expected=bind?['action','object_path','sha256','size','type','content']:finalize?['action','object_path','content']:['action','object_path']
  if (Object.keys(body).length!==expected.length || expected.some(key=>!Object.hasOwn(body,key)) ||
      typeof body.object_path!=='string' || !pathPattern.test(body.object_path)) return res.status(400).end()
  if (bind && (typeof body.sha256!=='string'||!/^[0-9a-f]{64}$/.test(body.sha256)||
      !Number.isSafeInteger(body.size)||Number(body.size)<1||Number(body.size)>MAX_BYTES||
      !['video/mp4','video/webm'].includes(String(body.type)))) return res.status(400).end()
  if((finalize||bind) && (typeof body.content!=='string'||body.content.length>10000)) return res.status(400).end()
  const token=String(req.headers.authorization).slice(7)
  const client=createClient(url,anon,{global:{headers:{Authorization:'Bearer '+token}},auth:{persistSession:false,autoRefreshToken:false}})
  const authenticate=async()=>{
    const {data,error}=await client.auth.getUser(token)
    if(error||!data.user) throw Error('unauthorized')
    return data.user.id
  }
  try {
    const owner=await authenticate(),path=body.object_path
    if(pathPattern.exec(path)?.[1]!==owner) return res.status(403).end()
    if(bind) {
      const {data,error}=await client.rpc('video_bind_recovery_manifest_v1',{p_path:path,p_sha256:body.sha256,p_size:body.size,p_type:body.type,p_content:body.content})
      if(error||!Number.isSafeInteger(data)) return res.status(409).json({error:'recovery_binding_unavailable'})
      if(await authenticate()!==owner) return res.status(401).end()
      return res.status(200).json({bound:true,expires:data})
    }
    const state=async()=>{
      const {data,error}=await client.rpc('video_recovery_state_v1',{p_path:path})
      if(error||!data||data.owner!==owner||data.path!==path) throw Error('unavailable')
      return data
    }
    const before=await state()
    if(finalize && body.content!==before.content) return res.status(409).json({error:'recovery_content_mismatch'})
    if(before.active!==true) return res.status(410).json({error:'recovery_expired'})
    if(finalize && !before.generation) return res.status(409).json({error:'recovery_object_missing'})
    if(!before.generation) return res.status(200).json({state:'waiting_for_upload',allow_resume:false,expires:before.expires})
    const response=await fetch(url+'/storage/v1/object/authenticated/post-videos/'+path,{
      headers:{apikey:anon,Authorization:'Bearer '+token},redirect:'error',signal:AbortSignal.timeout(30000),cache:'no-store',
    })
    if(!response.ok||!response.body) throw Error('unavailable')
    const reader=response.body.getReader(),chunks:Buffer[]=[]
    let size=0
    try {
      const declared=response.headers.get('content-length')
      if(response.headers.get('content-type')?.split(';')[0]?.trim().toLowerCase()!==before.type ||
        (declared!==null&&(!/^[0-9]+$/.test(declared)||Number(declared)!==before.size))) throw Error('media mismatch')
      while(true) {
        const {done,value}=await reader.read();if(done)break
        size+=value.byteLength
        if(size>MAX_BYTES||size>before.size) throw Error('oversize')
        chunks.push(Buffer.from(value))
      }
    } finally {await reader.cancel().catch(()=>undefined);reader.releaseLock()}
    if(size!==before.size) throw Error('incomplete')
    const inspected=await inspectStagedVideo(Buffer.concat(chunks,size),path.endsWith('.mp4')?'mp4':'webm',size)
    if(inspected.sha256!==before.sha256) return res.status(409).json({error:'recovery_file_mismatch'})
    if(await authenticate()!==owner) return res.status(401).end()
    const after=await state()
    // Detect generation/manifest/post races. This is advisory; finalize MUST
    // repeat verification and enforce the atomic generation fence itself.
    if(JSON.stringify(before)!==JSON.stringify(after)||after.active!==true) return res.status(409).json({error:'recovery_state_changed'})
    if(after.post_id && (after.post_generation!==after.generation||after.post_sha256!==inspected.sha256||after.post_duration!==Math.round(inspected.duration*1000)/1000)) {
      return res.status(409).json({error:'recovery_post_mismatch'})
    }
    if(finalize) {
      // This synthetic-key configuration is accepted ONLY beyond the exact
      // localhost + explicit isolated-mode fence above. Production stays off.
      const keyHex=process.env.VIDEO_RECOVERY_ISOLATED_KEY_HEX
      if(!keyHex||!/^[0-9a-f]{64}$/.test(keyHex)) return res.status(503).json({error:'recovery_signer_unavailable'})
      const nonce=createVideoAttestationNonce(),expires=Math.floor(Date.now()/1000)+120
      const key=Buffer.from(keyHex,'hex')
      let signature:string
      try {signature=signBinaryVideoAttestation(key,{owner,path,generation:after.generation,sha256:inspected.sha256,
        durationMs:Math.round(inspected.duration*1000),contentSha256:videoAttestationDigest(body.content as string),expiresAt:expires,nonce})}
      finally {key.fill(0)}
      if(await authenticate()!==owner) return res.status(401).end()
      const {data,error}=await client.rpc('video_publish_recovered_attested_v1',{p_owner:owner,p_path:path,
        p_generation:after.generation,p_sha256:inspected.sha256,p_duration_ms:Math.round(inspected.duration*1000),
        p_content:body.content,p_expires_at:expires,p_nonce:nonce,p_signature:signature,p_key_id:1})
      if(error||typeof data!=='string'||!/^[0-9a-f-]{36}$/.test(data)) return res.status(409).json({error:'recovery_publication_unconfirmed'})
      return res.status(200).json({state:'published',post_id:data})
    }
    return res.status(200).json({state:after.post_id?'published':'verified_ready',allow_resume:false,
      content:after.content,post_id:after.post_id,generation:after.generation,sha256:inspected.sha256,size,ffprobe_verified:true,expires:after.expires})
  } catch {return res.status(409).json({error:'recovery_unavailable'})}
}
