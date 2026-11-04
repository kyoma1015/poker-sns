import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { FIRST_RELEASE_ENABLED, firstReleaseVerdict } from '../src/firstReleasePolicy.ts'
const doc=JSON.parse(readFileSync('docs/progress/FIRST_RELEASE_V1.json','utf8'))
const bytes=readFileSync(doc.legacy_ledger.path)
const blob=createHash('sha1').update(Buffer.from('blob '+bytes.length+'\0')).update(bytes).digest('hex')
const legacy=JSON.parse(bytes)
const count=Object.keys(legacy.current_snapshot.features).filter(k=>/^(sns|tda|diag)\./.test(k)).length
const preserved=blob===doc.legacy_ledger.git_blob && count===32
const result=firstReleaseVerdict(doc)
const report={candidate:'first-release-v1',legacy_ledger_preserved:preserved,legacy_product_rows:count,
 passed:doc.gates.filter(g=>g.status==='PASS').length,total:doc.gates.length,blocked:result.blocked,
 runtime_enabled:FIRST_RELEASE_ENABLED,verdict:preserved && result.ready && FIRST_RELEASE_ENABLED?'GO':'NO-GO'}
console.log(JSON.stringify(report,null,2))
if(process.argv.includes('--check') && report.verdict!=='GO')process.exitCode=2
