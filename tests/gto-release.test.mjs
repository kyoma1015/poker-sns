import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { handLabels, queryKey, validateVerifiedRange } from '../src/gto/rangeCatalog.ts'
import { sha256, canonicalJson, rangePayloadDigest, findIntegrityCheckedRange } from '../src/gto/rangeIntegrity.ts'
import { generateReleaseCandidates, sealReviewedCandidate, candidateDigest } from '../src/gto/releaseCandidate.ts'
import { oneBBRange, oneBBCertificate } from '../src/gto/oneBBRange.ts'

// Synthetic transport-only fixtures, never app registry data or GTO proof.
async function fixture() {
  const query = { format: 'mtt', players: 2, seat: 0, stackBb: '50', anteBb: '0', rakePct: '0',
    rakeCapBb: null, openBb: '2.5', threeBetBb: '9', fourBetBb: '21', stage: 'rfi', history: [] }
  const record = { schema: 'pokerid-verified-preflop-v1', id: 'synthetic-release-only', query,
    conditionClass: 'explicit_test', conditionName: 'Synthetic transport test', policyDigest: 'a'.repeat(64),
    configDigest: 'b'.repeat(64), certificateId: 'synthetic-review', actions: ['Fold', 'Call', 'Raise'],
    hands: Object.fromEntries(handLabels.map(h => [h, { combinations: h.endsWith('s') ? 4 : h.endsWith('o') ? 12 : 6,
      frequencies: [.25,.5,.25], evBb: .1, evIntervalBb: [.1,.1], actionEvBb: [0,.1,.2], actionEvIntervalBb: [[0,0],[.1,.1],[.2,.2]] }])),
    coverage: { combinations: 1326, hands: 169 }, equilibriumVerified: true }
  const certificate = { datasetId: record.id, queryKey: queryKey(query), policyDigest: record.policyDigest,
    configDigest: record.configDigest, artifactSha256: 'c'.repeat(64), scope: 'complete_target_game',
    continuation: 'full_native_game', metric: 'max_unilateral_deviation_gain', upperBoundBb: .001,
    acceptedToleranceBb: .01, reviewReference: 'synthetic transport only', confidence: 1,
    verificationMethod: 'deterministic_full_game', rangePayloadSha256: await rangePayloadDigest(record) }
  return { record, certificate, registry: { 'synthetic-review': certificate } }
}
const source = JSON.parse(await readFile(new URL('../src/gto/independentResearchData.json', import.meta.url)))
const evidence = JSON.parse(await readFile(new URL('../docs/qa/suit-exact-preflop-20261106/results.json', import.meta.url)))

test('canonical content hash uses WebCrypto SHA256 and stable object key ordering', async () => {
  assert.equal(await sha256('abc'), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
  assert.equal(canonicalJson({z:1,a:[2,3]}), canonicalJson({a:[2,3],z:1}))
  assert.throws(() => canonicalJson([undefined]))
  assert.throws(() => canonicalJson({x:Infinity}))
})
test('ordinary display needs a reviewed payload digest; legacy HU1BB is preserved', async () => {
  const { record, certificate, registry } = await fixture()
  assert.equal((await findIntegrityCheckedRange(record.query, [record], registry))?.id, record.id)
  delete certificate.rangePayloadSha256
  assert.ok(validateVerifiedRange(record, registry)) // structure is not content binding
  assert.equal(await findIntegrityCheckedRange(record.query, [record], registry), null)
  assert.equal((await findIntegrityCheckedRange(oneBBRange.query, [oneBBRange], { [oneBBRange.certificateId]:oneBBCertificate }))?.id, oneBBRange.id)
})
test('coherent frequency and EV tampering cannot reuse a reviewed certificate', async () => {
  const { record, registry } = await fixture()
  record.hands.AA.frequencies=[.25,.25,.5];record.hands.AA.evBb=.125;record.hands.AA.evIntervalBb=[.125,.125]
  assert.ok(validateVerifiedRange(record,registry))
  assert.equal(await findIntegrityCheckedRange(record.query,[record],registry),null)
})
test('actionEV shape, intervals and weighted EV consistency fail closed', async () => {
  for (const mutate of [r=>{delete r.hands.AA.actionEvIntervalBb},r=>{r.hands.AA.actionEvBb=[0,.1,.3]},
    r=>{delete r.hands.AA.actionEvBb[1]},r=>{r.hands.AA.actionEvIntervalBb[1]=[.2,.3]}]) {
    const {record,registry}=await fixture();mutate(record)
    assert.equal(validateVerifiedRange(record,registry),null)
  }
})
test('actual full-policy evidence yields8 blocked candidates/1352 rows with exact histories and actionEV', async () => {
  const candidates=await generateReleaseCandidates(source,evidence)
  assert.equal(candidates.length,8)
  for (const c of candidates) {
    assert.equal(Object.keys(c.draft.hands).length,169)
    assert.equal(c.draft.equilibriumVerified,false)
    assert.equal(c.blockers.length,5)
    assert.equal(await sealReviewedCandidate(c,{}),null)
    assert.equal(c.evaluatedF64lePolicyDigest,evidence.models[c.modelId].root_expected_game_bounds_bb.policy_digest_before)
    assert.notEqual(c.draft.policyDigest,c.evaluatedF64lePolicyDigest) // full profile also binds continuation
    assert.notEqual(c.publishedJsonPolicyDigest,c.evaluatedF64lePolicyDigest) // two explicit encodings
    for(const h of handLabels) assert.deepEqual(c.draft.hands[h].frequencies,source.models[c.modelId].contexts[c.draft.query.stage].hands[h].frequencies)
  }
})
test('missing full policy, changed policy bytes and altered exported frequencies are rejected', async () => {
  await assert.rejects(generateReleaseCandidates(source),/完全な生成元方策/)
  const changed=structuredClone(evidence);changed.complete_preflop_policies.learned_small[0]+=.001
  await assert.rejects(generateReleaseCandidates(source,changed),/識別子|完全な/)
  const bad=structuredClone(source);bad.models.learned_small.contexts.rfi.hands.AA.frequencies=[1,0,0]
  await assert.rejects(generateReleaseCandidates(bad,evidence),/同一性/)
})
test('review sealing binds candidate, complete-game review, full payload and formal condition review', async () => {
  const {record,certificate}=await fixture()
  const candidate={schema:'pokerid-preflop-release-candidate-v1',id:record.id,status:'BLOCKED_UNVERIFIED',
    canonicalSourceSha256:'d'.repeat(64),canonicalEvidenceSha256:'e'.repeat(64),modelId:'synthetic-only',
    publishedJsonPolicyDigest:'a'.repeat(64),evaluatedF64lePolicyDigest:'a'.repeat(64),
    draft:{...record,equilibriumVerified:false},modelNashconvIntervalBb:[0,.001],blockers:['synthetic-only']}
  const review={candidateSha256:await candidateDigest(candidate),certificateId:record.certificateId,certificate,
    conditionClass:record.conditionClass,conditionName:record.conditionName,
    fullGameAndEvReview:{reference:'synthetic full-game/EV fixture only',evidenceSha256:certificate.artifactSha256}}
  assert.equal((await sealReviewedCandidate(candidate,{[candidate.id]:review}))?.id,record.id)
  const changed=structuredClone(candidate);changed.draft.hands.AA.evBb=.2
  assert.equal(await sealReviewedCandidate(changed,{[candidate.id]:review}),null)
  review.conditionClass='formal'
  assert.equal(await sealReviewedCandidate(candidate,{[candidate.id]:review}),null)
})
test('independent BR arithmetic cannot be replaced by a small labelled convergence number', async () => {
  const a=structuredClone(source),b=structuredClone(evidence)
  a.models.learned_small.independent_python_br.br_sb_ev_bb+=1
  b.models.learned_small.independent_python_br.br_sb_ev_bb+=1
  await assert.rejects(generateReleaseCandidates(a,b),/独立BR/)
  const missingA=structuredClone(source),missingB=structuredClone(evidence)
  delete missingA.models.learned_small.independent_python_br.profile_sb_ev_bb
  delete missingB.models.learned_small.independent_python_br.profile_sb_ev_bb
  await assert.rejects(generateReleaseCandidates(missingA,missingB),/独立BR/)
})
