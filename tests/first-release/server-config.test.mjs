import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
const config=JSON.parse(readFileSync('vercel.first-release.json','utf8'))
assert.equal(config.buildCommand,'node scripts/build-first-release.mjs')
assert.equal(config.outputDirectory,'dist-first-release')
assert.equal(config.routes.length,3)
const [deny,files,spa]=config.routes
assert.equal(deny.status,404)
assert.equal(deny.dest,undefined)
assert.equal(deny.headers['Cache-Control'],'private, no-store, max-age=0')
assert.equal(deny.headers['X-Robots-Tag'],'noindex, nofollow')
assert.equal(files.handle,'filesystem')
assert.deepEqual(spa,{src:'/.*',dest:'/index.html'})
// Static path-policy checks, not a provider routing emulator.
const pattern=new RegExp(deny.src)
const blocked=['/api','/api/','/api/share','/api/og','/api/poker-id-image','/api/anything/new','/share','/share/player-type/fixture','/share/poker-id/fixture','/share/tournament/fixture','/API/share','/Share/player-type/fixture']
for(const path of blocked) assert.equal(pattern.test(path),true,path)
for(const path of ['/timeline','/search','/dm','/profile','/assets/main.js','/apiculture','/shared']) assert.equal(pattern.test(path),false,path)
const gate=JSON.parse(readFileSync('docs/progress/FIRST_RELEASE_V1.json','utf8'))
assert.equal(gate.initial_release_enabled,false)
assert.equal(gate.verdict,'NO-GO')
assert.equal(gate.gates.find(x=>x.id==='nested_and_api_deferral').status,'BLOCKED')
console.log('PASS: candidate server config contract; 12 denied paths, 7 non-denied paths. Static contract only; remote RPC/encoded path/provider runtime UNKNOWN.')
