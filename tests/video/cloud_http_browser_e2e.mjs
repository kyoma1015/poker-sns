import assert from 'node:assert/strict'
import {createServer} from 'node:http'
import {randomUUID,createHash} from 'node:crypto'
import {chromium} from 'playwright-core'
import {createCloudVideoHandler} from '../../server/video-cloud-http.mjs'
import {createVideoMediaHandler} from '../../api/video-media.ts'
export async function verifyCloudHttp({owner,other,bytes,key,url,signingKey,sql}) {
 assert.equal(url,'http://127.0.0.1:56321')
 process.env.VITE_SUPABASE_URL=url;process.env.VITE_SUPABASE_ANON_KEY=key
 process.env.VIDEO_CLOUD_TEST_HMAC_HEX=signingKey.toString('hex');process.env.VIDEO_CLOUD_TEST_HMAC_ID='7'
 const publish=createCloudVideoHandler({isolatedLocalOnly:true}),media=createVideoMediaHandler({isolatedLocalOnly:true})
 const server=createServer(async(req,res)=>{
 res.status=code=>{res.statusCode=code;return res};res.json=x=>res.end(JSON.stringify(x));res.send=x=>res.end(x)
 if(req.url==='/'){res.setHeader('Content-Type','text/html');return res.end('<!doctype html><title>Cloud HTTP isolated test</title>')}
 let raw='';for await(const c of req)raw+=c
 req.body=raw?JSON.parse(raw):undefined;req.query={post_id:req.url.split('/').pop()}
 await(req.url==='/finalize'?publish:media)(req,res)
 })
 let browser
 try{
 await new Promise(r=>server.listen(0,'127.0.0.1',r))
 browser=await chromium.launch({headless:true,args:['--no-sandbox']})
 const page=await browser.newPage();await page.goto('http://127.0.0.1:'+server.address().port)
 const token=(await owner.auth.getSession()).data.session.access_token
 const foreign=(await other.auth.getSession()).data.session.access_token
 const uid=(await owner.auth.getUser()).data.user.id,path=uid+'/'+randomUUID()+'.mp4'
 const request=(body,jwt=token)=>page.evaluate(async({body,jwt})=>{const r=await fetch('/finalize',{method:'POST',headers:{Authorization:'Bearer '+jwt,'Content-Type':'application/json'},body:JSON.stringify(body)});return {status:r.status,body:await r.text()}},{body,jwt})
 const manifest={action:'reserve',object_path:path,sha256:createHash('sha256').update(bytes).digest('hex'),size:bytes.length,type:'video/mp4',content:'HTTP cloud publication'}
 assert.equal((await request(manifest)).status,201)
 assert.ifError((await owner.storage.from('post-videos').upload(path,bytes,{contentType:'video/mp4',upsert:false})).error)
 const body={object_path:path,content:manifest.content}
 assert.equal((await request(body,foreign)).status,503)
 const results=await Promise.all([request(body),request(body)])
 for(const r of results)assert.equal(r.status,201)
 const id=JSON.parse(results[0].body).post_id
 assert.equal(JSON.parse(results[1].body).post_id,id)
 const playback=await page.evaluate(async({id,token})=>{const r=await fetch('/media/'+id,{headers:{Authorization:'Bearer '+token}});const data=await r.blob();if(r.status!==200)return {status:r.status};const v=document.createElement('video');v.muted=true;v.src=URL.createObjectURL(data);document.body.append(v);await v.play();return {status:r.status,playing:!v.paused}},{id,token})
 assert.equal(playback.status,200);assert.equal(playback.playing,true)
 assert.equal(sql("select count(*) from public.posts where video_path='"+path+"'"),'1')
 console.log('PASS: dedicated cloud real HTTP + Chromium reservation, actual ffprobe/HMAC publish, concurrent one-post and JWT video playback; foreign finalize rejected')
 }finally{if(browser)await browser.close();await new Promise(r=>server.close(r));delete process.env.VIDEO_CLOUD_TEST_HMAC_HEX;delete process.env.VIDEO_CLOUD_TEST_HMAC_ID;delete process.env.VITE_SUPABASE_URL;delete process.env.VITE_SUPABASE_ANON_KEY}
}
