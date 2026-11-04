import assert from 'node:assert/strict'
import { test } from 'node:test'
import handler from '../api/poker-id-image.ts'

// Pure handler tests: every fetch is replaced; no real URL, key, DB or Storage is used.
const player='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
const other='bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
const cases=[
 ['invalid UUID',{id:'bad'},400,0],
 ['unsupported method',{method:'POST'},405,0],
 ['private or missing card',{cards:[]},404,1],
 ['failed visibility query',{cardStatus:503},500,1],
 ['wrong owner must not authorize image',{cards:[{user_id:other}]},500,1],
 ['JSON string must not authorize image',{cards:'unexpected rowset'},500,1],
 ['duplicate rows must not authorize image',{cards:[{user_id:player},{user_id:player}]},500,1],
 ['null rowset fails closed',{cards:null},500,1],
 ['missing private image',{storageStatus:404},404,2],
 ['valid public PNG',{},200,2],
 ['HEAD validates visibility without a response body',{method:'HEAD'},200,2],
 ['UUID casing remains accepted',{id:player.toUpperCase()},200,2],
]
for(const [name,options,expectedStatus,expectedCalls] of cases) {
 await test(name,async()=>{
  const previous={base:process.env.VITE_SUPABASE_URL,key:process.env.SUPABASE_SERVICE_ROLE_KEY,fetch:globalThis.fetch,error:console.error}
  const calls=[]
  const response={code:0,headers:{},body:undefined,status(code){this.code=code;return this},setHeader(k,v){this.headers[k]=v},send(body){this.body=body;return this},end(){return this}}
  try {
   process.env.VITE_SUPABASE_URL='https://fixture.invalid'
   process.env.SUPABASE_SERVICE_ROLE_KEY='fixture-only-not-a-credential'
   console.error=()=>{}
   globalThis.fetch=async(url,init)=>{
    const parsed=new URL(url)
    assert.equal(parsed.origin,'https://fixture.invalid','all external requests forbidden')
    assert.equal(init.cache,'no-store')
    calls.push(parsed.pathname)
    if(parsed.pathname==='/rest/v1/poker_id_cards'){
     assert.equal(parsed.searchParams.get('is_public'),'eq.true')
     assert.equal(parsed.searchParams.get('user_id'),'eq.'+(options.id??player))
     return new Response(JSON.stringify(Object.hasOwn(options,'cards')?options.cards:[{user_id:player}]),{status:options.cardStatus??200})
    }
    assert.equal(parsed.pathname,'/storage/v1/object/poker-id-card-og/'+(options.id??player)+'/card.png')
    return new Response(new Uint8Array([137,80,78,71]),{status:options.storageStatus??200})
   }
   await handler({method:options.method??'GET',query:{id:options.id??player}},response)
   assert.equal(response.code,expectedStatus)
   assert.equal(calls.length,expectedCalls,'unverified visibility must never reach Storage')
   if(expectedStatus===200){
    assert.equal(response.headers['Cache-Control'],'private, no-store, max-age=0')
    assert.equal(response.headers['X-Content-Type-Options'],'nosniff')
    assert.equal(response.headers['Content-Type'],'image/png')
    if(options.method==='HEAD')assert.equal(response.body,undefined)
    else assert.deepEqual(response.body,Buffer.from([137,80,78,71]))
   }
  } finally {
   globalThis.fetch=previous.fetch;console.error=previous.error
   if(previous.base===undefined)delete process.env.VITE_SUPABASE_URL;else process.env.VITE_SUPABASE_URL=previous.base
   if(previous.key===undefined)delete process.env.SUPABASE_SERVICE_ROLE_KEY;else process.env.SUPABASE_SERVICE_ROLE_KEY=previous.key
  }
 })
}
