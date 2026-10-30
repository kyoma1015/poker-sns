import assert from 'node:assert/strict'
import {createClient} from '@supabase/supabase-js'
import {createHash,randomUUID} from 'node:crypto'
import {createRecoveryMultitabFixture} from './isolated_recovery_multitab_fixture.mjs'
import {signBinaryVideoAttestation,videoAttestationDigest} from '../../server/video-attestation.js'

export async function createRecoveryIdentityFixture({url,anon,bytes,sql,dbUrl,call}) {
 assert.equal(url,'http://127.0.0.1:56321');assert.match(dbUrl,/127\.0\.0\.1:56322\//)
 const client=()=>createClient(url,anon,{auth:{persistSession:false,autoRefreshToken:false}})
 const good=client(),email=`identity-${randomUUID()}@example.invalid`,password='Disposable-Identity-Fixture1!'
 assert.ifError((await good.auth.signUp({email,password})).error)
 const uid=(await good.auth.getUser()).data.user.id,goodToken=(await good.auth.getSession()).data.session.access_token
 const sessionId=token=>JSON.parse(Buffer.from(token.split('.')[1],'base64url')).session_id
 let bad,losingToken,phase='revocation'
 const login=async()=>{
  bad=client();const result=await bad.auth.signInWithPassword({email,password});assert.ifError(result.error)
  losingToken=result.data.session.access_token
  assert.notEqual(sessionId(losingToken),sessionId(goodToken),'same owner must have independent real Auth sessions')
  return losingToken
 }
 await login()
 const path=uid+'/'+randomUUID()+'.webm',sha=createHash('sha256').update(bytes).digest('hex'),content='selective session deadline fixture'
 assert.ifError((await good.rpc('video_reserve_object_key',{p_owner:uid,p_path:path})).error)
 assert.equal((await call({action:'bind_recovery',object_path:path,sha256:sha,size:bytes.length,type:'video/webm',content},goodToken)).status,200)
 assert.ifError((await good.storage.from('post-videos').upload(path,bytes,{contentType:'video/webm',upsert:false})).error)
 const attempts=[]
 const core=createRecoveryMultitabFixture({owner:good,uid,url,path,bytes,sql,dbUrl,transformPublication:(args,headers)=>{
  const losing=headers.get('authorization')==='Bearer '+losingToken
  attempts.push({losing,phase})
  if(phase==='attestation'&&losing) {
   // Explicit trusted-server TTL fixture, never browser-controlled metadata.
   args={...args,p_expires_at:Math.floor(Date.now()/1000)+2}
   args.p_signature=signBinaryVideoAttestation(Buffer.from('41'.repeat(32),'hex'),{owner:uid,path,generation:args.p_generation,sha256:args.p_sha256,durationMs:args.p_duration_ms,contentSha256:videoAttestationDigest(args.p_content),expiresAt:args.p_expires_at,nonce:args.p_nonce})
  }
  return args
 }})
 const indexes=which=>attempts.flatMap((item,index)=>which(item)?[index]:[])
 const revoked=()=>indexes(item=>item.phase==='revocation'&&item.losing)
 const expired=()=>indexes(item=>item.phase==='attestation'&&item.losing)
 const shared=()=>indexes(item=>item.phase==='manifest')
 return {
  ...core,tokens:[losingToken,goodToken],
  async revokeLosingSession() {
   const oldSession=sessionId(losingToken)
   assert.ifError((await bad.auth.signOut({scope:'local'})).error)
   assert.equal(sql(`select count(*) from auth.sessions where id='${oldSession}' and user_id='${uid}';`),'0','only the selected actual Auth session was revoked')
   assert.equal(sql(`select count(*) from auth.sessions where id='${sessionId(goodToken)}' and user_id='${uid}';`),'1','competing valid session must survive')
   assert.ifError((await good.auth.getUser(goodToken)).error)
  },
  assertRevokedRejected(){assert.equal(revoked().length,1);core.assertRejected(revoked()[0],/recovery session unavailable/)},
  auditRevocation:()=>core.audit(1,2,{rejected:revoked()}),
  newLosingSession:login,
  shortenAttestation(token){assert.equal(token===losingToken,true);phase='attestation'},
  async waitLosingExpiry(){assert.equal(expired().length,1);await core.waitClaimExpiry(expired()[0])},
  assertLosingExpiryRejected(){core.assertRejected(expired()[0],/invalid attestation claims|recovery expired during publication/)},
  auditExpiry:()=>core.audit(1,4,{rejected:[...revoked(),...expired()]}),
  stopShortening(){phase='manifest'},
  async auditManifestExpiry(){
   assert.equal(shared().length,2)
   for(const index of shared())core.assertRejected(index,/recovery manifest mismatch or expired/)
   return core.audit(1,6,{rejected:[...revoked(),...expired(),...shared()],active:false})
  },
 }
}
