import assert from 'node:assert/strict'
import {createClient} from '@supabase/supabase-js'
import {createHash,createHmac,randomUUID} from 'node:crypto'
import {execFileSync} from 'node:child_process'
import {createRecoveryMultitabFixture} from './isolated_recovery_multitab_fixture.mjs'

export async function createRecoveryExpiryFixture({kind,url,anon,bytes,sql,dbUrl,call,localJwtSecret}) {
 assert.equal(url,'http://127.0.0.1:56321');assert.match(dbUrl,/127\.0\.0\.1:56322\//)
 assert.ok(['jwt','reservation-published','reservation-unpublished','reservation-precommit'].includes(kind))
 const client=()=>createClient(url,anon,{auth:{persistSession:false,autoRefreshToken:false}})
 const good=client(),bad=client(),email=`expiry-${randomUUID()}@example.invalid`,password='Disposable-Expiry-Fixture1!'
 assert.ifError((await good.auth.signUp({email,password})).error)
 assert.ifError((await bad.auth.signInWithPassword({email,password})).error)
 const goodToken=(await good.auth.getSession()).data.session.access_token,badToken=(await bad.auth.getSession()).data.session.access_token
 const claims=token=>JSON.parse(Buffer.from(token.split('.')[1],'base64url'))
 const uid=claims(goodToken).sub
 assert.equal(claims(badToken).sub,uid);assert.notEqual(claims(badToken).session_id,claims(goodToken).session_id)
 const path=uid+'/'+randomUUID()+'.webm',sha=createHash('sha256').update(bytes).digest('hex'),content='real JWT and reservation exp '+kind
 assert.ifError((await good.rpc('video_reserve_object_key',{p_owner:uid,p_path:path})).error)
 assert.equal((await call({action:'bind_recovery',object_path:path,sha256:sha,size:bytes.length,type:'video/webm',content},goodToken)).status,200)
 assert.ifError((await good.storage.from('post-videos').upload(path,bytes,{contentType:'video/webm',upsert:false})).error)
 let shortToken,shortExp
 const attempts=[]
 const core=createRecoveryMultitabFixture({owner:good,uid,url,path,bytes,sql,dbUrl,transformPublication:(args,headers)=>{
  attempts.push({short:headers.get('authorization')==='Bearer '+shortToken})
  return args // Never change attestation claims or signatures in these cases.
 }})
 const auth=token=>fetch(url+'/auth/v1/user',{headers:{apikey:anon,Authorization:'Bearer '+token},cache:'no-store',redirect:'error'})
 const rest=token=>fetch(url+'/rest/v1/rpc/video_recovery_state_v1',{method:'POST',headers:{apikey:anon,Authorization:'Bearer '+token,'Content-Type':'application/json'},body:JSON.stringify({p_path:path}),cache:'no-store',redirect:'error'})
 return {
  ...core,kind,tokens:[badToken,goodToken],
  async publishBaseline() {
   assert.equal((await call({action:'recovery_finalize',object_path:path,content},goodToken)).status,200)
   return core.audit(1,1)
  },
  async mintShortJwt() {
   assert.equal(kind,'jwt')
   // Read only the disposable local signing material, never print it. Prefer
   // CLI status; older CLI output may require the exact local Auth container.
   let secret=localJwtSecret
   if(!secret) {
    let values
    try{values=JSON.parse(execFileSync('docker',['inspect','--format','{{json .Config.Env}}','supabase_auth_pokerid-video-isolated'],{encoding:'utf8',stdio:['ignore','pipe','pipe']}))}
    catch{throw Error('disposable Auth signing material unavailable; raw diagnostics withheld')}
    secret=values.find(value=>value.startsWith('GOTRUE_JWT_SECRET='))?.slice('GOTRUE_JWT_SECRET='.length)
   }
   assert.equal(typeof secret,'string','disposable JWT signer must be available');assert.ok(secret.length>=32)
   const now=Math.floor(Date.now()/1000)
   shortExp=now+3
   const payload={...claims(badToken),iat:now,exp:shortExp}
   const header=Buffer.from(JSON.stringify({alg:'HS256',typ:'JWT'})).toString('base64url')
   const encoded=Buffer.from(JSON.stringify(payload)).toString('base64url'),unsigned=header+'.'+encoded
   shortToken=unsigned+'.'+createHmac('sha256',secret).update(unsigned).digest('base64url')
   secret=undefined
   const beforeAuth=await auth(shortToken);assert.equal(beforeAuth.status,200,'actual GoTrue must accept the short signed session JWT before expiry')
   const beforeRest=await rest(shortToken);assert.equal(beforeRest.status,200,'actual PostgREST must accept its signature/claims before expiry')
   assert.ok(Number(sql('select extract(epoch from clock_timestamp());'))<shortExp,'token must remain valid before dispatching actual finalize')
   return shortToken
  },
  async waitJwtExpiry() {
   for(let n=0;n<200;n++) {
    if(Number(sql('select extract(epoch from clock_timestamp());'))>=shortExp)return
    await new Promise(resolve=>setTimeout(resolve,20))
   }
   throw Error('actual JWT exp did not cross on DB wall clock')
  },
  async assertJwtRejected() {
   const indexes=attempts.flatMap((attempt,index)=>attempt.short?[index]:[])
   assert.equal(indexes.length,1);core.assertRejected(indexes[0],/recovery JWT expired/)
   assert.equal(sql(`select count(*) from auth.sessions where id='${claims(badToken).session_id}' and user_id='${uid}';`),'1','session stays present: failure must be JWT exp, not revocation')
   const result=await auth(shortToken)
   assert.ok([401,403].includes(result.status),'actual Auth rejects the expired JWT')
   const data=await result.json();assert.match(String(data.msg??data.message??data.error_description),/expired/i,'Auth denial must explicitly identify expiry')
   assert.equal((await call({action:'recovery_finalize',object_path:path,content},shortToken)).status,409,'expired JWT retry is denied by actual API auth before any signed publication')
   return core.audit(1,2,{rejected:indexes})
  },
  async assertPostgrestExpiry() {
   // PostgREST permits clock skew. Observe its actual admission rejection,
   // without changing either service clock or weakening the strict DB fence.
   const until=Date.now()+45000
   while(Date.now()<until) {
    const response=await rest(shortToken)
    if(response.status===401){const data=await response.json();assert.match(String(data.message),/JWT expired/i);return}
    assert.equal(response.status,200,'only the documented temporary skew allowance may precede REST expiry')
    await new Promise(resolve=>setTimeout(resolve,1000))
   }
   throw Error('PostgREST never rejected the expired JWT at the real admission boundary')
  },
  async auditReservationExpired() {
   const baseline=kind==='reservation-published'?1:0
   for(let index=baseline;index<baseline+2;index++)core.assertRejected(index,kind==='reservation-precommit'?/recovery reservation unavailable|recovery expired during publication/:/recovery reservation unavailable/)
   if(kind==='reservation-precommit'){
    const messages=core.rejectionMessages()
    assert.equal(messages.filter(message=>/recovery expired during publication/.test(message)).length,1,'one request must reach the final deadline check after parent publication')
    assert.equal(messages.filter(message=>/recovery reservation unavailable/.test(message)).length,1,'the serialized competitor observes expiry at reservation acquisition')
   }
   const id=await core.audit(baseline,baseline+2,{rejected:[baseline,baseline+1],active:false})
   const retry=await call({action:'recovery_finalize',object_path:path,content},goodToken)
   assert.equal(retry.status,410,'expired reservation cannot resume on a fresh actual API request')
   return core.audit(baseline,baseline+2,{rejected:[baseline,baseline+1],active:false}).then(next=>{assert.equal(next,id);return id})
  },
 }
}
