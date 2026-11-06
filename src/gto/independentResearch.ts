import data from './independentResearchData.json' with { type: 'json' }
import { canonicalQuery, handLabels } from './rangeCatalog.ts'
import type { RangeQuery } from './rangeCatalog.ts'

export type IndependentStage = 'rfi' | 'vs_open' | 'vs_3bet' | 'vs_4bet'
export type IndependentHand = { frequencies: number[]; action_ev_bb: number[]; ev_bb: number; reach_mass: number;
  action_ev_intervals_bb: number[][]; model_ev_interval_bb: number[] }
type Context = { actor: number; actions: string[]; history: string[]; coverage: number; hands: Record<string, IndependentHand> }
type Model = { contexts: Record<IndependentStage, Context>; sample_game_nashconv_bb: number; evaluation_sample_nashconv_bb: number;
  policy_digest: string; game_scope: string; root_expected_game_bounds_bb: { preflop_nashconv_interval: number[] } }
export type IndependentData = { schema: string; models: Record<string, Model>; full_game_gto_verified: boolean;
  ordinary_catalog_admission: string; real_game_approximation_error: string; external_gto_comparison: string;
  confidence_simultaneous_both_oracles: number | null; uncertainty_kind?: string; numeric_guard_bb?: number; numeric_guard_is_formal_rounding_proof?: boolean; formal_acceptance_complete: number; protocol_sha256: string;
  condition: { players: number; stack_bb: number; ante_bb: number; rake_pct: number; raise_to_bb: number[]; formal_profile: boolean };
  quality: { sample_game_convergence: boolean; expected_game_root_NC_upper_at_most0_1: boolean };
  oracle_summary: Record<string, { samples: number; exact_board_fraction: number; unique_physical_flops: number; represented_physical_flops?: number }> }
export const independentResearch = data as unknown as IndependentData
export const independentQuery: RangeQuery = { format: 'mtt', players: 2, seat: 0, stackBb: '50', anteBb: '0',
  rakePct: '0', rakeCapBb: null, openBb: '2.5', threeBetBb: '9', fourBetBb: '21', stage: 'rfi' }
export const independentStages: IndependentStage[] = ['rfi', 'vs_open', 'vs_3bet', 'vs_4bet']
export const histories: Record<IndependentStage, string> = { rfi: '自分までアクションなし', vs_open: 'SBが2.5BBへオープン',
  vs_3bet: 'SB 2.5BB → BB 9BB', vs_4bet: 'SB 2.5BB → BB 9BB → SB 21BB' }
const expectedActions: Record<IndependentStage, string[]> = { rfi: ['fold', 'call', 'raise_to_5'], vs_open: ['fold', 'call', 'raise_to_18'],
  vs_3bet: ['fold', 'call', 'raise_to_42'], vs_4bet: ['fold', 'call', 'raise_to_100'] }
const expectedHistories: Record<IndependentStage, string[]> = { rfi: [], vs_open: ['raise_to_5'],
  vs_3bet: ['raise_to_5', 'raise_to_18'], vs_4bet: ['raise_to_5', 'raise_to_18', 'raise_to_42'] }
const finite = (x: number) => typeof x === 'number' && Number.isFinite(x)
const interval = (xs: number[], x: number) => Array.isArray(xs) && xs.length === 2 && xs.every(finite) && xs[0] <= x + 1e-9 && x <= xs[1] + 1e-9
export function findIndependentResearch(value: unknown, source: unknown = independentResearch): IndependentStage | null {
  try {
    const q = canonicalQuery(value), d = source as IndependentData, c = d.condition
    const exact = d.schema === 'pokerid-independent-preflop-research-v2'
    if ((!exact && d.schema !== 'pokerid-independent-preflop-research-v1') || d.full_game_gto_verified !== false ||
      d.ordinary_catalog_admission !== 'REJECTED_RESEARCH_ONLY' || d.formal_acceptance_complete !== 0 ||
      d.real_game_approximation_error !== 'UNKNOWN' || d.external_gto_comparison !== 'NOT PERFORMED' ||
      (exact ? d.confidence_simultaneous_both_oracles !== null || d.uncertainty_kind !== 'enumerated_population_with_empirical_rounding_guard' || d.numeric_guard_bb !== 1e-7 || d.numeric_guard_is_formal_rounding_proof !== false : d.confidence_simultaneous_both_oracles !== .99) || !c || c.formal_profile !== false ||
      c.players !== 2 || c.stack_bb !== 50 || c.ante_bb !== 0 || c.rake_pct !== 0 || JSON.stringify(c.raise_to_bb) !== '[2.5,9,21,50]' ||
      q.players !== 2 || q.stackBb !== '50' || q.anteBb !== '0' || q.rakePct !== '0' || q.rakeCapBb !== null ||
      q.openBb !== '2.5' || q.threeBetBb !== '9' || q.fourBetBb !== '21' || !independentStages.includes(q.stage as IndependentStage)) return null
    const stage = q.stage as IndependentStage
    if (q.seat !== (stage === 'rfi' || stage === 'vs_3bet' ? 0 : 1) ||
      Object.keys(d.models).sort().join(',') !== 'learned_large,learned_small') return null
    for (const model of Object.values(d.models)) {
      if (!Array.isArray(model.root_expected_game_bounds_bb?.preflop_nashconv_interval) || model.root_expected_game_bounds_bb.preflop_nashconv_interval.length !== 2 || model.root_expected_game_bounds_bb.preflop_nashconv_interval.some(x => !finite(x) || x < 0) || model.root_expected_game_bounds_bb.preflop_nashconv_interval[0] > model.root_expected_game_bounds_bb.preflop_nashconv_interval[1]) return null
      if (!finite(model.sample_game_nashconv_bb) || model.sample_game_nashconv_bb < 0 || !finite(model.evaluation_sample_nashconv_bb)) return null
      for (const s of independentStages) {
        const context = model.contexts[s]
        if (context.actor !== (s === 'rfi' || s === 'vs_3bet' ? 0 : 1) || context.coverage !== 169 ||
          JSON.stringify(context.actions) !== JSON.stringify(expectedActions[s]) || JSON.stringify(context.history) !== JSON.stringify(expectedHistories[s]) || Object.keys(context.hands).length !== 169) return null
        for (const label of handLabels) {
          const row = context.hands[label]
          if (!row || row.frequencies.length !== 3 || row.action_ev_bb.length !== 3 || row.action_ev_intervals_bb.length !== 3 ||
            row.frequencies.some(x => !finite(x) || x < 0 || x > 1) || Math.abs(row.frequencies.reduce((a, b) => a + b, 0) - 1) > 1e-9 ||
            !finite(row.ev_bb) || !interval(row.model_ev_interval_bb, row.ev_bb) ||
            row.action_ev_bb.some((x, i) => !finite(x) || !interval(row.action_ev_intervals_bb[i], x))) return null
        }
      }
    }
    return stage
  } catch { return null }
}
