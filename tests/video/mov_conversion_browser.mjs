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
  // Guard the Safari composer poster fallback even when no new frame callback fires.
  const timelineSource = await readFile('src/Timeline.tsx', 'utf8')
  assert.match(timelineSource, /onSeeked=\{event => captureVideoPreviewPoster\(event\.currentTarget\)\}/)
  assert.match(timelineSource, /onLoadedData=\{event => captureVideoPreviewPoster\(event\.currentTarget\)\}/)
  assert.match(timelineSource, /onCanPlay=\{event => captureVideoPreviewPoster\(event\.currentTarget\)\}/)
  assert.match(timelineSource, /requestVideoFrameCallback/)
  assert.match(timelineSource, /expectedUrl !== videoPreviewUrlRef\.current/)
  // Keep click receipt and disabled-state diagnostics visible without altering upload logic.
  assert.match(timelineSource, /if \(videoFile \|\| pendingVideoRef\.current\) setMessage\('投稿操作を受け付けました。安全条件を確認しています。'\)/)
  assert.match(timelineSource, /!canSubmitPost \? '投稿ボタンが無効です。添付の選択状態を確認してください。動画の再送信は行いません。'/)
  assert.match(timelineSource, /if \(!VIDEO_SERVER_ENABLED\) \{/)
  assert.match(timelineSource, /if \(postSubmitInFlightRef\.current\) \{/)
  // A video blocked by API/recovery safety gates must not look submittable.
  assert.match(timelineSource, /disabled=\{isPosting \|\| !canSubmitPost \|\| \(Boolean\(videoFile \|\| pendingVideo\) && \(!VIDEO_SERVER_ENABLED \|\| videoRecoveryBlocked\)\)\}/)
  const source = await readFile('src/videoMovConversion.ts', 'utf8')
  // Safari can omit ended for short MOVs: source time must independently stop recording.
  assert.match(source, /video\.currentTime >= duration - 0\.05/)
  assert.match(source, /performance\.now\(\) - playbackStartedAt > \(duration \+ 4\) \* 1000/)
  assert.match(source, /video\.paused && !resumeAttempted/)
  assert.match(source, /video\.muted = false/, 'Decoded audio capture requires unmuting in Chrome')
  assert.match(source, /再生位置 /)
  assert.match(source, /video\.onended = stopAtSourceEnd/)
  assert.match(source, /window\.clearInterval\(playbackWatchdog\)/)
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
  // Compare decoded PCM of the known-audible source with the output, not just track metadata.
  // This runs locally in Chrome CI and does not claim to validate Safari's Web Audio path.
  const pcmRms=path=>{
    const pcm=execFileSync('ffmpeg',['-v','error','-i',path,'-vn','-ac','1','-ar','48000','-f','f32le','pipe:1'])
    assert.ok(pcm.length>0 && pcm.length%4===0,'PCM decode must return complete samples')
    let energy=0
    for(let i=0;i<pcm.length;i+=4) energy+=pcm.readFloatLE(i)**2
    return Math.sqrt(energy/(pcm.length/4))
  }
  const sourceRms=pcmRms(fixture)
  const convertedRms=pcmRms(output)
  assert.ok(sourceRms>0.02,'test source must contain audible PCM')
  assert.ok(convertedRms>0.02,'converted MP4 must contain audible PCM')
  assert.ok(convertedRms/sourceRms>0.05,'converted audio unexpectedly attenuated relative to source')
  console.log('PASS MOV -> H264/audio MP4, duration/size and source/output decoded PCM RMS')
  // Simulate the Safari muted-media Web Audio path in Chrome. Chromium is not
  // Safari: this only proves that silent decoded PCM cannot be published.
  await page.evaluate(() => {
    Object.defineProperty(navigator, 'userAgent', {
      configurable: true,
      value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'
    })
  })
  // Safari UA alone must no longer force the capture source into mute.
  // This uses Chrome's decoder and is NOT evidence of Safari device success.
  const safariLike=await convert(fixture)
  assert.equal(safariLike.ok,true,safariLike.error)
  console.log('PASS Safari-like UA captures non-muted Web Audio in Chrome (not Safari validation)')
  // Deliberately force a muted media element to simulate Safari returning
  // silence; the conversion must still fail closed without publishing bytes.
  await page.evaluate(() => {
    const originalPlay = HTMLMediaElement.prototype.play
    HTMLMediaElement.prototype.play = function (...args) {
      this.muted = true
      this.defaultMuted = true
      return originalPlay.apply(this, args)
    }
    window.restoreMediaPlay = () => { HTMLMediaElement.prototype.play = originalPlay }
  })
  const mutedAudio=await convert(fixture)
  assert.equal(mutedAudio.ok,false,'Silent Web Audio must never produce a publishable MP4')
  assert.match(mutedAudio.error,/音声|再生|変換/)
  await page.evaluate(() => window.restoreMediaPlay())
  console.log('PASS forced-muted Web Audio fails closed without upload (not Safari device validation)')
  await page.evaluate(() => {
    Object.defineProperty(navigator, 'userAgent', { configurable: true, value: 'Chrome/130.0.0.0' })
  })
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
  const long=join(qa,'long.mov')
  execFileSync('ffmpeg',['-v','error','-f','lavfi','-i','color=c=blue:size=64x64:rate=1','-t','31','-c:v','libx264','-pix_fmt','yuv420p','-y',long])
  const tooLong=await convert(long)
  assert.equal(tooLong.ok,false);assert.match(tooLong.error,/30秒/)
  await page.evaluate(()=>{MediaRecorder.isTypeSupported=()=>false})
  const unsupported=await convert(fixture)
  assert.equal(unsupported.ok,false);assert.match(unsupported.error,/MP4/)
  assert.equal(external,0)
  console.log('PASS corrupt/oversize/31-second/unsupported-encoder fail closed, zero external requests')
} finally {
  await browser?.close()
  if(server) await new Promise(resolve=>server.close(resolve))
  await rm(qa,{recursive:true,force:true})
}
