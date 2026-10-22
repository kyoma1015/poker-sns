import test from 'node:test'
import assert from 'node:assert/strict'
import { parseQuizQuestions, safeQuizRpc, auditQuizQuestions, quizAuditReport } from '../src/tdaQuizData.ts'
const question = () => ({ question_id: 'q1', question_text: '正しい判断は？', difficulty: null, category: 'TDA', options: [
  { id: 'a', option_order: 2, option_text: '行動A' }, { id: 'b', option_order: 1, option_text: '行動B' },
] })
test('question validation sorts a copy without changing option identity or original input', () => {
  const input = [question()]
  const parsed = parseQuizQuestions(input)
  assert.deepEqual(parsed[0].options.map(o => o.id), ['b','a'])
  assert.deepEqual(input[0].options.map(o => o.id), ['a','b'])
  assert.deepEqual(parseQuizQuestions([]), [])
})
for (const [name, value] of [ ['null',null], ['object',{}], ['no options',[{...question(),options:null}]], ['one option',[{...question(),options:[question().options[0]]}]], ['empty text',[{...question(),question_text:'  '}]], ['missing metadata',[{...question(),category:undefined}]], ['duplicate question ID',[question(),question()]], ['duplicate option ID',[{...question(),options:[question().options[0],question().options[0]]}]], ['duplicate option order',[{...question(),options:question().options.map(o=>({...o,option_order:1}))}]], ['fractional order',[{...question(),options:question().options.map(o=>({...o,option_order:.5}))}]], ['empty option text',[{...question(),options:question().options.map(o=>({...o,option_text:''}))}]], ['negative order',[{...question(),options:question().options.map(o=>({...o,option_order:-1}))}]] ]) {
  test(`malformed ${name} fails closed`, () => assert.throws(() => parseQuizQuestions(value)))
}
test('rejected and synchronous transport failures become recoverable errors without retries', async () => {
  let calls = 0
  const result = await safeQuizRpc(() => { calls++; return Promise.reject(new Error('network')) })
  assert.equal(result.data, null); assert.ok(result.error); assert.equal(calls,1)
  assert.ok((await safeQuizRpc(() => { throw new Error('sync') })).error)
})
test('successful save data and RPC permission errors are preserved without reinterpretation', async () => {
  const data = { data: [{ is_correct: false }], error:null }
  assert.equal(await safeQuizRpc(() => Promise.resolve(data)), data)
  const failure = { data:null, error:{code:'42501',message:'permission denied'} }
  assert.equal(await safeQuizRpc(() => Promise.resolve(failure)), failure)
})
test('offline audit flags normalized question and option duplicate candidates only', () => {
  const q1=question(); q1.question_text='Ａ B'; q1.options[1].option_text='行 動 A'
  const q2={...question(),question_id:'q2',question_text:'a　b'}
  const report=auditQuizQuestions([q1,q2])
  assert.deepEqual(report.duplicateQuestionCandidates,[['q1','q2']])
  assert.deepEqual(report.duplicateOptionCandidates,[{question_id:'q1',option_ids:['b','a']}])
  assert.equal(report.official_rule_accuracy,'UNVERIFIED')
})

test('audit report flags missing expected count and never claims publication approval', () => {
  const report = quizAuditReport([question()], 350)
  assert.equal(report.question_count,1)
  assert.equal(report.count_matches,false)
  assert.equal(report.publication_approved,false)
  assert.equal(report.official_rule_accuracy,'UNVERIFIED')
  assert.equal(report.verdict,'REVIEW_REQUIRED')
  assert.equal(quizAuditReport([question()],1).verdict,'STRUCTURE_PASS')
  assert.throws(() => quizAuditReport([question()], Infinity))
})

for (const [label,value] of [
 ['empty sparse question bank',Array(1)],
 ['question followed by missing row',Object.assign(Array(2),{0:question()})],
 ['entirely missing options',[{...question(),options:Array(2)}]],
 ['one present option',[{...question(),options:Object.assign(Array(2),{0:question().options[0]})}]],
]) test(`sparse quiz input rejects ${label}`,()=>assert.throws(()=>parseQuizQuestions(value)))
test('frozen dense valid input and empty bank remain valid',()=>{
 const q=question();Object.freeze(q.options);Object.freeze(q);const bank=Object.freeze([q]);
 assert.equal(parseQuizQuestions(bank)[0].options.length,2);assert.deepEqual(parseQuizQuestions([]),[])
})

test('reviewed PR28 empty-audit guard remains present',()=>assert.equal(quizAuditReport([]).verdict,'REVIEW_REQUIRED'))
