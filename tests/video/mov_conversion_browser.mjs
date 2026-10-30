// Disposable browser media test. No Supabase, JWT, credentials or external network.
import assert from 'node:assert/strict'
import { readFile, writeFile, mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { execFileSync } from 'node:child_process'
import { createServer } from 'node:http'
import ts from 'typescript'
import { chromium } from 'playwright-core'

const qa = await mkdtemp(join(tmpdir(), 'poker-mov-'))
let browser
let server
try {
  const source = await readFile('src/videoMovConversion.ts', 'utf8')
  const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText
  const fixture = join(qa, 'camera.mov')
  execFileSync('ffmpeg', ['-v','error','-f','lavfi','-i','testsrc2=size=320x240:rate=30','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','2','-c:v','libx264','-profile:v','baseline','-pix_fmt','yuv420p','-c:a','aac','-y',fixture])
  const html = `<!doctype html><input type="file"><button id="convert">変換</button><button id="abort">中止</button><output></output><script type="module">
    import {convertMovToMp4} from '/convert.js';
    let controller;
    document.querySelector('#abort').onclick=()=>controller?.abort();
    document.querySelector('#convert').onclick=async()=>{
      controller=new AbortController(); window.result=null;
      try { const output=await convertMovToMp4(document.querySelector('input').files[0],controller.signal);
        window.result={ok:true,type:output.type,size:output.size,bytes:Array.from(new Uint8Array(await output.arrayBuffer()))};
      } catch(e) {window.result={ok:false,error:e.message};}
      document.querySelector('output').textContent=window.result.ok?'MP4変換完了':window.result.error;
    };
  </script>`
  server = createServer((req,res) => {res.setHeader('Content-Type',req.url==='/convert.js'?'text/javascript':'text/html');res.end(req.url==='/convert.js'?js:html)})
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve))
  browser=await chromium.launch({channel:'chrome',headless:true,args:['--no-sandbox']})
  const page=await browser.newPage()
  let external=0
  await page.route('**/*',route=>{if(new URL(route.request().url()).hostname!=='127.0.0.1'){external++;return route.abort()}return route.continue()})
  await page.goto(`http://127.0.0.1:${server.address().port}`)
  async function convert(path,abort=false) {
    await page.locator('input').setInputFiles(path)
    await page.locator('#convert').click()
    if(abort) await page.locator('#abort').click()
    await page.waitForFunction(()=>window.result!==null,{},{timeout:60000})
    return page.evaluate(()=>window.result)
  }
  console.log('MP4 encoder support', await page.evaluate(()=>['video/mp4;codecs=avc1.42E01E,mp4a.40.2','video/mp4;codecs=avc1,mp4a.40.2','video/mp4;codecs=avc1,opus'].map(type=>({type,supported:MediaRecorder.isTypeSupported(type)}))))
  const converted=await convert(fixture)
  assert.equal(converted.ok,true,converted.error)
  assert.equal(converted.type,'video/mp4')
  assert.ok(converted.size>0&&converted.size<=20*1024*1024)
  const output=join(qa,'converted.mp4')
  await writeFile(output,Buffer.from(converted.bytes))
  const probe=JSON.parse(execFileSync('ffprobe',['-v','error','-show_streams','-show_format','-of','json',output],{encoding:'utf8'}))
  console.log('Output codecs',probe.streams.map(s=>({type:s.codec_type,codec:s.codec_name})))
  assert.ok(probe.streams.some(s=>s.codec_type==='video'&&s.codec_name==='h264'))
  assert.ok(probe.streams.some(s=>s.codec_type==='audio'&&['aac','opus'].includes(s.codec_name)))
  assert.ok(Math.abs(Number(probe.format.duration)-2)<0.4)
  // Verify decoded audio samples, not merely an advertised/silent audio track.
  const pcm=execFileSync('ffmpeg',['-v','error','-i',output,'-vn','-ac','1','-ar','48000','-f','f32le','pipe:1'])
  let energy=0
  for(let i=0;i<pcm.length;i+=4) energy+=pcm.readFloatLE(i)**2
  assert.ok(Math.sqrt(energy/(pcm.length/4))>0.02,'source audio must remain audible')
  console.log('PASS MOV -> H264/audio MP4, duration/size and decoded audible audio')
  const aborted=await convert(fixture,true)
  assert.equal(aborted.ok,false)
  assert.match(aborted.error,/中止/)
  console.log('PASS abort produces no output')
  const corrupt=join(qa,'corrupt.mov');await writeFile(corrupt,'not a movie')
  const bad=await convert(corrupt)
  assert.equal(bad.ok,false);assert.match(bad.error,/元の動画は送信していません/)
  const oversized=join(qa,'large.mov');await writeFile(oversized,Buffer.alloc(20*1024*1024+1))
  const large=await convert(oversized)
  assert.equal(large.ok,false);assert.match(large.error,/20MiB/)
  assert.equal(external,0)
  console.log('PASS corrupt/oversize fail closed, zero external requests')
} finally {
  await browser?.close()
  if(server) await new Promise(resolve=>server.close(resolve))
  await rm(qa,{recursive:true,force:true})
}
