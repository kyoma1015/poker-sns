import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {validate,measure,compare,compareTests,implementationMeasure,compareImplementation,verifyImplementationEvidence} from '../scripts/measure-abd-progress.mjs'
const base=JSON.parse(readFileSync(new URL('../docs/progress/ABD_PROGRESS.json',import.meta.url)))
const clone=()=>structuredClone(base)
test('frozen required scope and strict completion-evidence counts are reproducible',()=>{const r=measure(base,'baseline_snapshot');assert.deepEqual(r.product,{required:32,done:0,not_complete_or_unknown:32,unknown:4});assert.equal(r.groups.sns.percent,0);assert.equal(r.groups.tda.percent,0);assert.equal(r.groups.diagnosis.percent,0);assert.equal(r.groups.audit.percent,40);assert.equal(r.groups.integration.percent,50)})
test('isolation and integration are not silently promoted to product release',()=>{const d=clone();d.current_snapshot.features['sns.dm'].status='統合確認済み';assert.equal(measure(d).groups.sns.done,0)})
test('public-ready claim without every mandatory gate is refused',()=>{const d=clone();d.current_snapshot.features['sns.dm'].status='公開可能';assert.throws(()=>measure(d),/gate incomplete/)})
test('duplicate catalogue IDs and duplicate blockers fail closed',()=>{const d=clone();d.catalogue.push({...d.catalogue[0]});assert.throws(()=>validate(d),/duplicate feature/);const e=clone();e.current_snapshot.blockers.push({...e.current_snapshot.blockers[0]});assert.throws(()=>validate(e),/duplicate blocker/)})
test('UNKNOWN remains distinct from not-started and whole-product rate remains unknown',()=>{const r=measure(base);assert.equal(r.groups.diagnosis.unknown,1);assert.equal(r.groups.diagnosis.states['未着手'],0);assert.equal(r.overall_percent,null);assert(!Object.hasOwn(r.groups,'gto'))})
test('catalogue identity change requires a new baseline and cannot alter denominator silently',()=>{const d=clone();delete d.current_snapshot.features['sns.dm'];assert.throws(()=>validate(d),/frozen catalogue/)})
test('test additions or different suites cannot masquerade as quality improvement',()=>{assert.throws(()=>compareTests({suite_id:'a',total:1,pass:1,fail:0},{suite_id:'b',total:1,pass:1,fail:0}),/different suites/);assert.throws(()=>compareTests({suite_id:'a',total:1,pass:1,fail:0},{suite_id:'a',total:2,pass:2,fail:0}),/size changed/)})
test('baseline comparison separates six release blockers from two held blocked jobs',()=>{const r=compare(base);assert.deepEqual(r.retained_tests.pass,[381,381]);assert.deepEqual(r.retained_tests.fail,[0,0]);assert.deepEqual(r.blockers,[6,6]);assert.equal(base.held_state_note.blocked,2);assert.equal(r.overall_percent,null)})

test('implementation is separate from v1 release evidence and keeps the exact denominator',()=>{
 const d=clone(), r=implementationMeasure(d)
 for(const [k,g]of Object.entries(r.groups))assert.equal(g.required,measure(d).groups[k].required)
 assert.equal(measure(d).groups.tda.percent,0)
 assert(r.groups.tda.implemented>0)
 assert.equal(r.groups.tda.percent,null)
 assert(r.groups.tda.unknown>0)
})
test('implementation claims require source, tests, exact commit and successful matching CI',()=>{
 for(const key of ['sources','tests','commit','ci','contract']){
  const d=clone(), row=Object.values(d.implementation_metric.snapshots.current_snapshot.features).find(r=>r.state==='IMPLEMENTED')
  row[key]=['sources','tests'].includes(key)?[]:null
  assert.throws(()=>implementationMeasure(d))
 }
})
test('source existence or isolated status cannot silently become implemented',()=>{
 const d=clone(),before=implementationMeasure(d).groups.sns.implemented
 d.current_snapshot.features['sns.search'].status='隔離テスト合格'
 assert.equal(implementationMeasure(d).groups.sns.implemented,before)
})
test('missing implementation row fails closed instead of shrinking required scope',()=>{
 const d=clone();delete d.implementation_metric.snapshots.current_snapshot.features['sns.dm']
 assert.throws(()=>implementationMeasure(d),/frozen catalogue/)
})
test('implementation evidence rejects mismatched CI HEAD or unpinned blob',()=>{
 const d=clone(), row=Object.values(d.implementation_metric.snapshots.current_snapshot.features).find(r=>r.state==='IMPLEMENTED')
 row.ci.head='0'.repeat(40);assert.throws(()=>implementationMeasure(d),/CI evidence/)
 const e=clone(),other=Object.values(e.implementation_metric.snapshots.current_snapshot.features).find(r=>r.state==='IMPLEMENTED')
 other.sources[0].blob='main';assert.throws(()=>implementationMeasure(e),/pinned blob/)
})
test('unknown implementation rate is never zero and never invents change points',()=>{
 const r=compareImplementation(base)
 assert.equal(r.sns.before.percent,null);assert.equal(r.sns.after.percent,null)
 assert.equal(r.sns.points,null);assert.equal(r.sns.confirmed_points,0)
 assert.equal(implementationMeasure(base).overall_percent,null)
})

test('implementation source and test blobs exist in pinned historical Git objects',()=>{
 assert.equal(verifyImplementationEvidence(base),true)
 const d=clone(),row=Object.values(d.implementation_metric.snapshots.current_snapshot.features).find(r=>r.state==='IMPLEMENTED')
 row.sources[0].blob='0'.repeat(40)
 assert.throws(()=>verifyImplementationEvidence(d),/historical blob/)
})
