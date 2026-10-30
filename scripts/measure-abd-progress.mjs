import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createHash} from 'node:crypto'
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
export function implementationMeasure(data,snapshot='current_snapshot'){
 validate(data)
 const metric=data.implementation_metric
 assert.equal(metric?.version,'abd-implementation-evidence-v1','implementation policy required')
 const s=metric.snapshots[snapshot];assert(s,'implementation snapshot required')
 assert.deepEqual(Object.keys(s.features).sort(),data.catalogue.map(f=>f.id).sort(),'implementation frozen catalogue')
 const groups={}
 for(const [id] of Object.entries(data.groups)){
  const fs=data.catalogue.filter(f=>f.group===id), rows=fs.map(f=>s.features[f.id])
  for(const row of rows){
   assert(['IMPLEMENTED','PARTIAL','NOT_STARTED','UNKNOWN'].includes(row.state),'implementation state')
   if(row.state==='IMPLEMENTED'){
    assert(typeof row.contract==='string'&&row.contract.length>0,'explicit implementation acceptance required')
    assert(/^[0-9a-f]{40}$/.test(row.commit),'implementation pinned commit')
    assert(row.sources.length>0&&row.tests.length>0,'source and test evidence required')
    for(const e of [...row.sources,...row.tests]){
     assert(typeof e.path==='string'&&e.path.length>0&&/^[0-9a-f]{40}$/.test(e.blob),'pinned blob evidence')
    }
    assert(Number.isSafeInteger(row.ci?.run_id)&&row.ci.run_id>0&&row.ci.head===row.commit&&row.ci.conclusion==='success','exact-head CI evidence required')
   }
  }
  const implemented=rows.filter(r=>r.state==='IMPLEMENTED').length,unknown=rows.filter(r=>r.state==='UNKNOWN').length
  groups[id]={required:fs.length,implemented,known_incomplete:rows.filter(r=>['PARTIAL','NOT_STARTED'].includes(r.state)).length,unknown,
   confirmed_percent:Math.round(implemented*10000/fs.length)/100,
   percent:unknown?null:Math.round(implemented*10000/fs.length)/100}
 }
 return {policy:metric.version,groups,overall_percent:null,note:'confirmed_percent is an evidence lower bound; exact percent remains UNKNOWN where any feature is UNKNOWN; implementation is never publication approval'}
}
export function verifyImplementationEvidence(data){
 implementationMeasure(data)
 const modes=new Set()
 for(const snapshot of Object.values(data.implementation_metric.snapshots)){
  for(const row of Object.values(snapshot.features)){
   if(row.state!=='IMPLEMENTED')continue
   for(const e of [...row.sources,...row.tests]){
    // Full checkout verifies historical commit/path. Shallow CI cannot assert
    // that mapping; it must still prove exact current bytes, never skip a row.
    let bytes
    try {
     execFileSync('git',['cat-file','-e',row.commit+'^{commit}'],{stdio:'pipe'})
     bytes=execFileSync('git',['show',row.commit+':'+e.path])
     modes.add('historical-commit-and-blob')
    } catch (error) {
     // A present commit with a missing path is invalid evidence, not shallow.
     try { execFileSync('git',['cat-file','-e',row.commit+'^{commit}'],{stdio:'pipe'}) }
     catch {
      bytes=readFileSync(e.path)
      modes.add('current-bytes-only-historical-mapping-unavailable')
     }
     if(bytes===undefined)throw error
    }
    const blob=createHash('sha1').update(Buffer.concat([Buffer.from('blob '+bytes.length),Buffer.from([0])])).update(bytes).digest('hex')
    assert.equal(blob,e.blob,'implementation historical blob '+e.path)
   }
  }
 }
 return {verified:true,modes:[...modes].sort()}
}
export function compareImplementation(data){
 const a=implementationMeasure(data,'baseline_snapshot'),b=implementationMeasure(data)
 return Object.fromEntries(Object.keys(a.groups).map(k=>[k,{before:a.groups[k],after:b.groups[k],confirmed_points:b.groups[k].confirmed_percent-a.groups[k].confirmed_percent,points:a.groups[k].percent===null||b.groups[k].percent===null?null:b.groups[k].percent-a.groups[k].percent}]))
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
 const evidence_verification=verifyImplementationEvidence(data)
 const head=execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim()
 console.log(JSON.stringify({evaluated_head:head,evaluated_at:new Date().toISOString(),snapshot:measure(data),comparison:compare(data),implementation:implementationMeasure(data),implementation_evidence:evidence_verification,implementation_comparison:compareImplementation(data),note:'evidence coverage, no stage weighting; unknown is not not-started; real DB and full GTO excluded from inferred success'},null,2))
}
