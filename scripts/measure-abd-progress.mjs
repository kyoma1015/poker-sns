import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {execFileSync} from 'node:child_process'
import {pathToFileURL} from 'node:url'
const states=new Set(['未着手','実装中','実装済み・未検証','隔離テスト合格','実DB認可確認済み','統合確認済み','公開可能','UNKNOWN'])
const gates=['scope','implementation','isolated_qa','db_auth','integration','release_review']
export function validate(data){
 assert.equal(data.schema_version,1)
 assert.equal(data.version,'abd-feature-evidence-v1')
 const ids=new Set()
 for(const f of data.catalogue){assert(!ids.has(f.id),'duplicate feature');ids.add(f.id);assert(data.groups[f.group],'unknown group');assert.equal(f.required,true)}
 for(const snap of [data.baseline_snapshot,data.current_snapshot]){
  assert.deepEqual(Object.keys(snap.features).sort(),[...ids].sort(),'frozen catalogue identity')
  assert(/^[0-9a-f]{40}$/.test(snap.assessed_commit),'pinned assessed source required')
  for(const [id,row]of Object.entries(snap.features)){
   assert(states.has(row.status),'unknown status')
   assert(Array.isArray(row.evidence))
   if(row.status==='公開可能'){
    assert(row.evidence.length,'completion needs evidence')
    assert(gates.every(g=>row.release_gates[g]===true),'product release gate incomplete')
   }
  }
  const blockers=new Set()
  for(const b of snap.blockers){assert(!blockers.has(b.id),'duplicate blocker');blockers.add(b.id)}
 }
 return data
}
export function measure(data,snapshot='current_snapshot'){
 validate(data);const s=data[snapshot];assert(s,'snapshot required');const groups={}
 for(const [id,group]of Object.entries(data.groups)){
  const fs=data.catalogue.filter(f=>f.group===id),rows=fs.map(f=>s.features[f.id])
  const done=rows.filter(r=>group.kind==='product'?r.status==='公開可能'&&gates.every(g=>r.release_gates[g]===true):['統合確認済み','公開可能'].includes(r.status)&&r.evidence.length>0).length
  groups[id]={required:fs.length,done,not_complete_or_unknown:fs.length-done,unknown:rows.filter(r=>r.status==='UNKNOWN').length,percent:Math.round(done*10000/fs.length)/100,kind:group.kind,states:Object.fromEntries([...states].map(state=>[state,rows.filter(r=>r.status===state).length]))}
 }
 const products=Object.values(groups).filter(g=>g.kind==='product')
 return {policy:data.version,assessed_commit:s.assessed_commit,at:s.at,groups,
  product:{required:products.reduce((n,g)=>n+g.required,0),done:products.reduce((n,g)=>n+g.done,0),not_complete_or_unknown:products.reduce((n,g)=>n+g.not_complete_or_unknown,0),unknown:products.reduce((n,g)=>n+g.unknown,0)},
  open_blockers:s.blockers.filter(b=>b.status==='OPEN').length,overall_percent:null,overall_reason:data.calculation.overall,tests:s.tests}
}
export function compareTests(before,after){
 assert.equal(before.suite_id,after.suite_id,'different suites must not be compared')
 assert.equal(before.total,after.total,'suite size changed; separate additions')
 for(const s of [before,after]){assert.equal(s.pass+s.fail,s.total);assert(s.pass>=0&&s.fail>=0)}
 return {suite_id:before.suite_id,total:before.total,pass:[before.pass,after.pass],fail:[before.fail,after.fail]}
}
export function compare(data){
 const a=measure(data,'baseline_snapshot'),b=measure(data)
 return {groups:Object.fromEntries(Object.keys(a.groups).map(k=>[k,{before:a.groups[k].percent,after:b.groups[k].percent,points:b.groups[k].percent-a.groups[k].percent}])),
 product_done:[a.product.done,b.product.done],product_incomplete:[a.product.not_complete_or_unknown,b.product.not_complete_or_unknown],blockers:[a.open_blockers,b.open_blockers],retained_tests:compareTests(a.tests.retained,b.tests.retained),overall_percent:null}
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const data=JSON.parse(readFileSync(process.argv[2]||'docs/progress/ABD_PROGRESS.json','utf8'))
 const head=execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim()
 console.log(JSON.stringify({evaluated_head:head,evaluated_at:new Date().toISOString(),snapshot:measure(data),comparison:compare(data),note:'evidence coverage, no stage weighting; unknown is not not-started; real DB and full GTO excluded from inferred success'},null,2))
}
