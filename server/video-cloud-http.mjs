import {createClient} from '@supabase/supabase-js'
import {randomBytes} from 'node:crypto'
import {assertCloudTestTarget} from './video-cloud-test-target.mjs'
import {inspectStagedVideo} from '../api/video-preflight.js'
import {signBinaryVideoAttestation,videoAttestationDigest} from './video-attestation.js'
export function createCloudVideoHandler(options = {}) {
return async function handleCloudVideo(req,res) {
 let stage = 'configuration'
 try {
 const local = options.isolatedLocalOnly === true && process.env.VITE_SUPABASE_URL === 'http://127.0.0.1:56321'
 const {url}=local ? {url:'http://127.0.0.1:56321'} : assertCloudTestTarget(process.env)
 if(req.method!=='POST')return res.status(405).end()
 const auth=req.headers.authorization
 if(typeof auth!=='string'||!/^Bearer [A-Za-z0-9_.-]+$/.test(auth))return res.status(401).end()
 const body=req.body
 if(!body||Object.getPrototypeOf(body)!==Object.prototype||Buffer.byteLength(JSON.stringify(body))>12288)return res.status(400).end()
 const client=createClient(url,process.env.VITE_SUPABASE_ANON_KEY,{global:{headers:{Authorization:auth}},auth:{persistSession:false,autoRefreshToken:false}})
 const identity=async()=>{const {data,error}=await client.auth.getUser(auth.slice(7));if(error||!data.user)throw Error('identity');const a=await client.rpc('video_cloud_allowed');if(a.error||a.data!==true)throw Error('allowlist');return data.user.id}
 stage = 'authentication'
 const uid=await identity()
 const path=body.object_path
 if(typeof path!=='string'||!new RegExp('^'+uid+'/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.](mp4|webm|mov)$').test(path))return res.status(403).end()
 if(body.action==='reserve'){
 const r=await client.rpc('video_cloud_reserve',{p_path:path,p_sha256:body.sha256,p_size:body.size,p_mime:body.type,p_content:body.content})
 if(r.error)return res.status(409).end()
 return res.status(201).json({reserved:true})
 }
 const recovering=body.action==='recover'
 if((body.action!==undefined&&!recovering)||(!recovering&&typeof body.content!=='string'))return res.status(400).end()
 const state=async()=>{const r=await client.rpc('video_cloud_state',{p_path:path});if(r.error||!r.data)throw Error('state');return r.data}
 stage = 'reservation_state'
 const before=await state()
 const content=recovering?before.content:body.content
 if(before.content!==content)throw Error('manifest')
 stage = 'storage_fetch'
 const media=await fetch(url+'/storage/v1/object/authenticated/post-videos/'+path,{headers:{apikey:process.env.VITE_SUPABASE_ANON_KEY,Authorization:auth},redirect:'error',signal:AbortSignal.timeout(30000),cache:'no-store'})
 if(!media.ok||!media.body||media.headers.get('content-type')?.split(';')[0]!==before.mime)throw Error('media')
 stage = 'storage_download'
 const reader=media.body.getReader(),chunks=[];let size=0
 try{while(true){const r=await reader.read();if(r.done)break;size+=r.value.length;if(size>20971520)throw Error('size');chunks.push(Buffer.from(r.value))}}finally{await reader.cancel().catch(()=>{})}
 stage = 'ffprobe_validation'
 const probe=await inspectStagedVideo(Buffer.concat(chunks),path.endsWith('.webm')?'webm':'mp4',before.size)
 if(probe.sha256!==before.sha256||await identity()!==uid||JSON.stringify(await state())!==JSON.stringify(before))throw Error('changed')
 stage = 'attestation_key'
 const key=process.env.VIDEO_CLOUD_TEST_HMAC_HEX
 if(!/^[0-9a-f]{64}$/.test(key||''))throw Error('key')
 const c={owner:uid,path,generation:before.generation,sha256:probe.sha256,durationMs:Math.round(probe.duration*1000),contentSha256:videoAttestationDigest(content),expiresAt:Math.floor(Date.now()/1000)+120,nonce:randomBytes(16).toString('hex')}
 const bytes=Buffer.from(key,'hex');let signature;try{signature=signBinaryVideoAttestation(bytes,c)}finally{bytes.fill(0)}
 if(await identity()!==uid)throw Error('identity')
 stage = 'publish_rpc'
 const r=await client.rpc('video_cloud_publish_v1',{p_owner:uid,p_path:path,p_generation:c.generation,p_sha256:c.sha256,p_duration_ms:c.durationMs,p_content:content,p_expires_at:c.expiresAt,p_nonce:c.nonce,p_signature:signature,p_key_id:Number(process.env.VIDEO_CLOUD_TEST_HMAC_ID)})
 if(r.error) { console.warn('video-cloud-test', 'publish_rpc_rejected'); return res.status(409).json({error:'publish_rpc_rejected'}) }
 return res.status(201).json({post_id:r.data})
 }catch(error){
 const reason = error instanceof Error && [
  'invalid stream structure', 'unsupported codec', 'invalid video dimensions',
  'invalid container', 'invalid video duration', 'missing streams',
  'ffprobe unavailable', 'ffprobe rejected video', 'ffprobe timeout',
  'invalid video size', 'downloaded bytes do not match expected object size',
  'ffprobe binary path must be absolute', 'invalid ffprobe JSON',
  'invalid ffprobe result', 'ffprobe output too large', 'ffprobe error output too large',
 ].includes(error.message) ? error.message : 'unclassified'
 console.warn('video-cloud-test', 'finalize_failed', stage, reason)
 return res.status(503).json({error:'cloud_finalize_failed',stage,reason})
 }
}

}
export const handleCloudVideo = createCloudVideoHandler()
