import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import vm from 'node:vm'
// Execute the actual component function with isolated DOM fault injection.
// This is not a browser/React E2E test and performs no network or DB access.
const source=readFileSync(new URL('../src/PlayerTypeDiagnosis.tsx',import.meta.url),'utf8')
const body=source.slice(source.indexOf('  function downloadShareImage('),source.indexOf('  async function saveShareImage('))
 .replace('blob: Blob','blob').replace(/: HTMLAnchorElement \| null/g,'')
function run(failure){
 const sentinel=Error(failure),state={removed:0,scheduled:0,revoked:0,clicked:0,appended:0}
 const link={remove(){state.removed++;if(failure==='remove')throw sentinel},click(){state.clicked++;if(failure==='click')throw sentinel}}
 const context={result:{result_type_key:'fox',result_id:'12345678-9'},URL:{createObjectURL:()=> 'blob:isolated',revokeObjectURL(){state.revoked++}},document:{createElement(){if(failure==='create')throw sentinel;return link},body:{appendChild(){state.appended++;if(failure==='append')throw sentinel}}},window:{setTimeout(fn,delay){assert.equal(delay,30000);state.scheduled++;fn()}}}
 vm.runInNewContext(body+';globalThis.execute=downloadShareImage',context)
 let error;try{context.execute({})}catch(e){error=e}
 return {state,error,sentinel,link}
}
test('successful PNG download preserves filename, click and delayed URL cleanup',()=>{
 const {state,error,link}=run();assert.equal(error,undefined);assert.equal(link.download,'PokerID_fox_12345678.png');assert.deepEqual(state,{removed:1,scheduled:1,revoked:1,clicked:1,appended:1})
})
for(const failure of ['create','append','click','remove'])test(`PNG ${failure} failure still schedules object URL cleanup and preserves exception`,()=>{
 const {state,error,sentinel}=run(failure);assert.equal(error,sentinel);assert.equal(state.scheduled,1);assert.equal(state.revoked,1)
 if(failure!=='create')assert.equal(state.removed,1)
})
