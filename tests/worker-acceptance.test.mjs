import assert from 'node:assert/strict'
import { parseQuizQuestions,quizAuditReport } from '../src/tdaQuizData.ts'
assert.deepEqual(parseQuizQuestions([]),[],'empty runtime RPC remains valid')
const empty=quizAuditReport([])
assert.equal(empty.verdict,'REVIEW_REQUIRED','empty offline audit must not pass')
assert.equal(empty.publication_approved,false)
const sample=[{question_id:'synthetic-id',question_text:'synthetic question',difficulty:null,category:null,options:[{id:'a',option_order:0,option_text:'a'},{id:'b',option_order:1,option_text:'b'}]}]
assert.equal(quizAuditReport(sample).verdict,'STRUCTURE_PASS')
assert.equal(quizAuditReport(sample).publication_approved,false)
console.log('PASS B immutable offline-empty acceptance')
