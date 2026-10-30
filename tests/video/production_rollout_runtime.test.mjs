import test from 'node:test'
import {Writable} from 'node:stream'
import mediaHandler from '../../api/video-media.ts'
import assert from 'node:assert/strict'
import {randomBytes,createHash} from 'node:crypto'
import {execFileSync} from 'node:child_process'
import {createProductionSupabaseVideoAdapters} from '../../api/video-production-supabase-adapters.ts'
import {finalizeImmutableCandidate} from '../../api/video-finalize-core.ts'
import handler from '../../api/video-finalize.ts'
import {signBinaryVideoAttestation,videoAttestationDigest} from '../../server/video-attestation.js'
const owner='11111111-1111-4111-8111-111111111111', generation='22222222-2222-4222-8222-222222222222', post='33333333-3333-4333-8333-333333333333'
const url='https://ephptepeuespnxtzdqby.supabase.co', path=owner+'/'+generation+'.mp4'
const response=()=>({statusCode:200,body:null,setHeader(){return this},status(n){this.statusCode=n;return this},json(x){this.body=x;return this},end(){return this}})
test('production adapter composes real ffprobe with attested RPC; stop preserves owner hide; target mismatch performs no I/O',async()=>{
  const names=['VITE_SUPABASE_URL','VITE_SUPABASE_ANON_KEY','VIDEO_PRODUCTION_FENCED_READY','VIDEO_PRODUCTION_LIMITED_ROLLOUT','VIDEO_ATTESTED_RPC_RELEASE_APPROVED','VIDEO_ALLOWED_USER_IDS','VIDEO_ATTESTATION_KEY_HEX','VIDEO_ATTESTATION_KEY_ID','VIDEO_SERVER_ENABLED','VIDEO_CLOUD_TEST_ENABLED']
  const saved=names.map(n=>process.env[n]), originalFetch=globalThis.fetch
  const key=randomBytes(32)
  try {
    delete process.env.VIDEO_CLOUD_TEST_ENABLED
    Object.assign(process.env,{VITE_SUPABASE_URL:url,VITE_SUPABASE_ANON_KEY:'synthetic-public-key',VIDEO_PRODUCTION_FENCED_READY:'true',VIDEO_PRODUCTION_LIMITED_ROLLOUT:'true',VIDEO_ATTESTED_RPC_RELEASE_APPROVED:'true',VIDEO_ALLOWED_USER_IDS:owner,VIDEO_ATTESTATION_KEY_HEX:key.toString('hex'),VIDEO_ATTESTATION_KEY_ID:'7',VIDEO_SERVER_ENABLED:'true'})
    const bytes=execFileSync(process.env.FFMPEG_BINARY_PATH||'ffmpeg',['-v','error','-f','lavfi','-i','color=c=black:s=32x32:d=1','-c:v','libx264','-movflags','frag_keyframe+empty_moov','-f','mp4','pipe:1'],{stdio:['ignore','pipe','pipe']})
    let writes=0,calls=0,identity=owner,allowed=true,mediaBytes=bytes
    globalThis.fetch=async(input,options={})=>{
      calls++
      const requestUrl=String(input instanceof Request?input.url:input)
      assert.ok(requestUrl.startsWith(url+'/'),'unexpected transport target')
      const json=x=>new Response(JSON.stringify(x),{headers:{'content-type':'application/json'}})
      if(requestUrl===url+'/auth/v1/user')return json({id:identity,app_metadata:{},user_metadata:{},aud:'authenticated'})
      if(requestUrl.endsWith('/rpc/video_rollout_allowed')||requestUrl.endsWith('/rpc/video_rollout_member'))return json(allowed)
      if(requestUrl.endsWith('/rpc/video_production_storage_generation'))return json(generation)
      if(requestUrl.includes('/rest/v1/posts?'))return json({user_id:owner,video_path:path})
      if(requestUrl.endsWith('/object/authenticated/post-videos/'+path))return new Response(mediaBytes,{headers:{'content-type':'video/mp4','content-length':String(mediaBytes.length)}})
      if(requestUrl.endsWith('/rpc/video_publish_attested_v1')){
        const p=JSON.parse(options.body)
        assert.equal(p.p_owner,owner);assert.equal(p.p_path,path);assert.equal(p.p_generation,generation)
        assert.equal(p.p_sha256,createHash('sha256').update(bytes).digest('hex'));assert.ok(p.p_duration_ms>0&&p.p_duration_ms<=30000)
        assert.equal(p.p_signature,signBinaryVideoAttestation(key,{owner,path,generation,sha256:p.p_sha256,durationMs:p.p_duration_ms,contentSha256:videoAttestationDigest(p.p_content),expiresAt:p.p_expires_at,nonce:p.p_nonce}))
        writes++;return json(post)
      }
      if(requestUrl.endsWith('/rpc/video_hide_own'))return json(true)
      throw Error('unexpected RPC; no network fallback permitted')
    }
    const adapter=()=>createProductionSupabaseVideoAdapters(url,'synthetic-public-key','synthetic.token')
    assert.equal(await finalizeImmutableCandidate('synthetic.token',path,'fixture',adapter()),post);assert.equal(writes,1)
    // Exercise an actual Node Writable/backpressure boundary above buffered-response size.
    mediaBytes=Buffer.alloc(5*1024*1024,7)
    let streamed=0,largest=0;const streamHash=createHash('sha256')
    const output=new Writable({highWaterMark:1024,write(chunk,encoding,done){streamed+=chunk.length;largest=Math.max(largest,chunk.length);streamHash.update(chunk);setImmediate(done)}})
    output.headers={};output.setHeader=(k,v)=>{output.headers[k]=v;return output};output.status=n=>{output.statusCode=n;return output};output.flushHeaders=()=>{output.headersSent=true};output.send=()=>{throw Error('large response must not buffer')}
    await mediaHandler({method:'GET',headers:{authorization:'Bearer synthetic.token'},query:{post_id:post}},output)
    assert.equal(output.statusCode,200);assert.equal(streamed,mediaBytes.length);assert.ok(largest<=65536)
    assert.equal(output.headers['Content-Length'],undefined);assert.equal(streamHash.digest('hex'),createHash('sha256').update(mediaBytes).digest('hex'))
    mediaBytes=bytes
    identity='44444444-4444-4444-8444-444444444444'
    await assert.rejects(finalizeImmutableCandidate('synthetic.token',path,'fixture',adapter()));assert.equal(writes,1)
    identity=owner;allowed=false
    await assert.rejects(finalizeImmutableCandidate('synthetic.token',path,'fixture',adapter()));assert.equal(writes,1)
    allowed=true;process.env.VIDEO_SERVER_ENABLED='false'
    await assert.rejects(finalizeImmutableCandidate('synthetic.token',path,'fixture',adapter()));assert.equal(writes,1)
    const body={action:'hide',post_id:post},req={method:'POST',headers:{authorization:'Bearer synthetic.token','content-type':'application/json','content-length':String(JSON.stringify(body).length)},body}
    const hidden=response();await handler(req,hidden);assert.equal(hidden.statusCode,200);assert.deepEqual(hidden.body,{hidden:true})
    process.env.VITE_SUPABASE_URL='https://hbhyuotzginwysrineyo.supabase.co'
    const before=calls,rejected=response();await handler(req,rejected);assert.equal(rejected.statusCode,503);assert.equal(calls,before)
  } finally {globalThis.fetch=originalFetch;key.fill(0);names.forEach((n,i)=>saved[i]===undefined?delete process.env[n]:process.env[n]=saved[i])}
})
