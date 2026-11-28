/** Offline release packaging, not a solver or a convergence certificate issuer.
 * Existing research data stays blocked until a separate trusted full-game review
 * binds the candidate, values and condition. No runtime upload or registry writes. */
import { independentStages, independentQuery, findIndependentResearch } from './independentResearch.ts'
import type { IndependentData } from './independentResearch.ts'
import { canonicalQuery, handLabels, validateVerifiedRange } from './rangeCatalog.ts'
import type { RangeQuery, ReviewedCertificate, VerifiedRange } from './rangeCatalog.ts'
import { canonicalJson, rangePayloadDigest, sha256 } from './rangeIntegrity.ts'
import layout from '../../gto/release/researchLayout.json' with { type: 'json' }

type Draft = Omit<VerifiedRange, 'certificate' | 'equilibriumVerified'> & { equilibriumVerified: false }
export type ReleaseCandidate = {
  schema: 'pokerid-preflop-release-candidate-v1'; id: string;
  status: 'BLOCKED_UNVERIFIED'; canonicalSourceSha256: string; canonicalEvidenceSha256: string; modelId: string;
  publishedJsonPolicyDigest: string; evaluatedF64lePolicyDigest: string;
  sourceActions: string[];
  modelReachMass: Record<string, number>;
  independentModelVerification: { nashconvBb: number; maxNativePythonDifferenceBb: number; scope: 'fixed_continuation_model_only' };
  draft: Draft; modelNashconvIntervalBb: [number, number]; blockers: string[];
}
export const releaseBlockers = [
  'FORMAL_CONDITION_NOT_REGISTERED', 'FULL_NATIVE_GAME_DEVIATION_BOUND_MISSING',
  'CONTINUATION_AND_ACTION_SPACE_ERROR_UNBOUNDED', 'REAL_GAME_ACTION_EV_NOT_VALIDATED',
  'NUMERIC_GUARD_IS_NOT_A_FORMAL_PROOF',
] as const
const hex = /^[a-f0-9]{64}$/
export async function generateReleaseCandidates(source: unknown, solverEvidence: unknown = source): Promise<ReleaseCandidate[]> {
  const data = source as IndependentData
  const evidence = solverEvidence as IndependentData & { complete_preflop_policies: Record<string, number[]> }
  const exportedEvidence = Object.fromEntries(Object.entries(evidence).filter(([key]) => !['source_sha256', 'oracle', 'complete_preflop_policies'].includes(key)))
  if (canonicalJson(exportedEvidence) !== canonicalJson(source)) throw new Error('生成元出力との同一性が不足しています。')
  const sourceDigest = await sha256(canonicalJson(source))
  const evidenceDigest = await sha256(canonicalJson(solverEvidence))
  const candidates: ReleaseCandidate[] = []
  for (const modelId of ['learned_small', 'learned_large'] as const) {
    const model = data?.models?.[modelId]
    if (!model || !hex.test(model.policy_digest)) throw new Error('方策の出典が不足しています。')
    const independent = (model as typeof model & { independent_python_br?: {
      abstract_nashconv_bb: number; br_sb_ev_bb: number; br_bb_min_sb_ev_bb: number; profile_sb_ev_bb: number };
      maximum_native_python_br_difference_bb?: number })
    const br = independent.independent_python_br, error = independent.maximum_native_python_br_difference_bb
    if (!br || [br.abstract_nashconv_bb, br.br_sb_ev_bb, br.br_bb_min_sb_ev_bb, br.profile_sb_ev_bb].some(x => typeof x !== 'number' || !Number.isFinite(x)) || typeof error !== 'number' || !Number.isFinite(error) || error < 0 || error > 1e-8 ||
        Math.abs(br.br_sb_ev_bb - br.br_bb_min_sb_ev_bb - br.abstract_nashconv_bb) > 1e-8 ||
        br.profile_sb_ev_bb < br.br_bb_min_sb_ev_bb - 1e-8 || br.profile_sb_ev_bb > br.br_sb_ev_bb + 1e-8 ||
        Math.abs(br.abstract_nashconv_bb - model.sample_game_nashconv_bb) > 1e-8) throw new Error('独立BRとモデル内利得の整合性が不足しています。')
    const bounds = model.root_expected_game_bounds_bb as typeof model.root_expected_game_bounds_bb & {
      policy_digest_before?: string; policy_digest_after?: string; policy_updated?: boolean }
    const fullPolicy = evidence?.complete_preflop_policies?.[modelId]
    if (!Array.isArray(fullPolicy) || fullPolicy.length !== layout.nodes.length * 3 * 169 ||
        fullPolicy.some(p => typeof p !== 'number' || !Number.isFinite(p) || p < 0 || p > 1) ||
        canonicalJson(evidence.models?.[modelId]) !== canonicalJson(model)) throw new Error('完全な生成元方策と独立評価の同一性が不足しています。')
    const bytes = new Uint8Array(fullPolicy.length * 8), view = new DataView(bytes.buffer)
    fullPolicy.forEach((p, i) => view.setFloat64(i * 8, p, true))
    const evaluatedDigest = await sha256(bytes)
    if (bounds.policy_digest_before !== evaluatedDigest || bounds.policy_digest_after !== evaluatedDigest || bounds.policy_updated !== false) throw new Error('独立評価と方策の識別子が一致しません。')
    const continuationDigest = (model as typeof model & { continuation_profile_digest?: string }).continuation_profile_digest
    if (!continuationDigest || !hex.test(continuationDigest)) throw new Error('継続方策の識別子が不足しています。')
    const completePolicyDigest = await sha256(canonicalJson({ preflopF64leSha256: evaluatedDigest,
      continuationProfileSha256: continuationDigest, gameScope: model.game_scope }))
    for (const stage of independentStages) {
      const context = model.contexts[stage]
      const nodeIndex = layout.nodes.findIndex(n => n.actor >= 0 && canonicalJson(n.history) === canonicalJson(context.history))
      const node = layout.nodes[nodeIndex]
      if (!node || node.actor !== context.actor || canonicalJson(node.actions) !== canonicalJson(context.actions)) throw new Error('元のアクション木と履歴が一致しません。')
      const legacy = { ...independentQuery, stage, seat: context?.actor }
      if (findIndependentResearch(legacy, source) !== stage) throw new Error('生成元の169ハンド・条件・研究識別が不整合です。')
      const history = context.history.map((action, i) => {
        if (!/^raise_to_\d+$/.test(action)) throw new Error('未対応の生成元履歴です。')
        return { seat: i % 2, action: 'raise' as const, toBb: String(Number(action.slice(9)) / 2) }
      })
      const query: RangeQuery = canonicalQuery({ ...legacy, history })
      const hands: VerifiedRange['hands'] = {}
      const modelReachMass: Record<string, number> = {}
      for (const [h, label] of handLabels.entries()) {
        const row = context.hands[label]
        if (typeof row.reach_mass !== 'number' || !Number.isFinite(row.reach_mass) || row.reach_mass < 0) throw new Error('生成元の到達質量が不正です。')
        modelReachMass[label] = row.reach_mass
        if (row.frequencies.some((p, a) => p !== fullPolicy[(nodeIndex * 3 + a) * 169 + h])) throw new Error('表示頻度が独立評価された完全方策と一致しません。')
        hands[label] = { combinations: label.endsWith('s') ? 4 : label.endsWith('o') ? 12 : 6,
          frequencies: [...row.frequencies], evBb: row.ev_bb,
          evIntervalBb: [row.model_ev_interval_bb[0], row.model_ev_interval_bb[1]],
          actionEvBb: [...row.action_ev_bb], actionEvIntervalBb: row.action_ev_intervals_bb.map(interval => [interval[0], interval[1]]) }
        if (Math.abs(row.frequencies.reduce((sum, p, i) => sum + p * row.action_ev_bb[i], 0) - row.ev_bb) > 1e-8) throw new Error('頻度加重EVが一致しません。')
      }
      const id = `candidate-${modelId}-${stage}-${sourceDigest.slice(0, 12)}`
      candidates.push({ schema: 'pokerid-preflop-release-candidate-v1', id,
        status: 'BLOCKED_UNVERIFIED', canonicalSourceSha256: sourceDigest, canonicalEvidenceSha256: evidenceDigest, modelId,
        publishedJsonPolicyDigest: model.policy_digest, evaluatedF64lePolicyDigest: evaluatedDigest,
        sourceActions: [...context.actions],
        modelReachMass,
        independentModelVerification: { nashconvBb: br.abstract_nashconv_bb, maxNativePythonDifferenceBb: error, scope: 'fixed_continuation_model_only' },
        modelNashconvIntervalBb: [...bounds.preflop_nashconv_interval] as [number, number], blockers: [...releaseBlockers],
        draft: { schema: 'pokerid-verified-preflop-v1', id, query, conditionClass: 'explicit_test',
          conditionName: '未検証：HU50BB・固定継続モデルのリリース候補',
          policyDigest: completePolicyDigest, configDigest: await sha256(canonicalJson({ query, condition: data.condition, gameScope: model.game_scope, layout })),
          certificateId: `pending-review-${id}`, actions: context.actions.map(action => {
            if (action === 'fold') return 'フォールド'
            if (action === 'check') return 'チェック'
            if (action === 'call') return stage === 'rfi' ? 'コール（リンプ）' : 'コール'
            if (!/^raise_to_\d+$/.test(action)) throw new Error('行動サイズが不明です。')
            const size = Number(action.slice(9)) / 2
            return size === 50 ? '50BBオールイン' : `${size}BBへレイズ`
          }), hands,
          coverage: { combinations: 1326, hands: 169 }, equilibriumVerified: false } })
    }
  }
  return candidates
}
export async function candidateDigest(candidate: ReleaseCandidate): Promise<string> {
  return sha256(canonicalJson(candidate))
}
export type ReleaseReview = {
  candidateSha256: string;
  // Independent full target-game/EV review references are trusted BUILD inputs,
  // never booleans supplied by candidate JSON or app users.
  fullGameAndEvReview: { reference: string; evidenceSha256: string };
  formalConditionReview?: { reference: string; evidenceSha256: string };
  certificateId: string; certificate: ReviewedCertificate;
  conditionClass: VerifiedRange['conditionClass']; conditionName: string;
}
export async function sealReviewedCandidate(candidate: ReleaseCandidate,
  reviews: Readonly<Record<string, ReleaseReview>>): Promise<VerifiedRange | null> {
  if (candidate.schema !== 'pokerid-preflop-release-candidate-v1' || candidate.status !== 'BLOCKED_UNVERIFIED' || candidate.draft.equilibriumVerified !== false) return null
  if (!Object.hasOwn(reviews, candidate.id)) return null
  const review = reviews[candidate.id]
  if (!review || review.candidateSha256 !== await candidateDigest(candidate) ||
      !review.fullGameAndEvReview?.reference || !hex.test(review.fullGameAndEvReview.evidenceSha256) ||
      review.fullGameAndEvReview.evidenceSha256 !== review.certificate?.artifactSha256 ||
      (review.conditionClass === 'formal' && (!review.formalConditionReview?.reference || !hex.test(review.formalConditionReview.evidenceSha256)))) return null
  const record = { ...candidate.draft, conditionClass: review.conditionClass, conditionName: review.conditionName,
    certificateId: review.certificateId, equilibriumVerified: true }
  const result = validateVerifiedRange(record, { [review.certificateId]: review.certificate })
  if (!result || !hex.test(review.certificate.rangePayloadSha256 ?? '') ||
      await rangePayloadDigest(result) !== review.certificate.rangePayloadSha256) return null
  return result
}
