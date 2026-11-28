import data from './precisionResearchData.json' with { type: 'json' }
import { handLabels } from './rangeCatalog.ts'
import type { AbstractStage } from './abstractResearch.ts'

export type ConditionalHand = { ev_bb: number; interval_bb: number[]; radius_bb: number; method: string;
  action_ev_bb: number[]; action_intervals_bb: number[][]; action_exact: boolean[] }
export function conditionalPrecision(mode: 'checkdown' | 'flop_controller', stage: AbstractStage, policy: string, actor: number, actions: string[]) {
  if (data.schema !== 'pokerid-research-conditional-ev-v1' || data.full_game_gto_verified !== false ||
    data.real_game_approximation_error !== null || data.confidence !== .99 || data.fixed_policy_digests[mode] !== policy) return null
  const context = data.models[mode].contexts[stage]
  if (context.actor !== actor || JSON.stringify(context.actions) !== JSON.stringify(actions) || Object.keys(context.hands).length !== 169) return null
  const hands = context.hands as Record<string, ConditionalHand>
  if (!handLabels.every(label => {
    const row = hands[label]
    return row && Number.isFinite(row.ev_bb) && Number.isFinite(row.radius_bb) && row.radius_bb >= 0 &&
      row.interval_bb.length === 2 && row.interval_bb.every(Number.isFinite) && row.interval_bb[0] <= row.ev_bb && row.ev_bb <= row.interval_bb[1] &&
      row.action_ev_bb.length === actions.length && row.action_ev_bb.every(Number.isFinite) &&
      row.action_intervals_bb.length === actions.length && row.action_exact.length === actions.length &&
      row.action_intervals_bb.every((ci, i) => ci.length === 2 && ci.every(Number.isFinite) && ci[0] <= row.action_ev_bb[i] && row.action_ev_bb[i] <= ci[1])
  })) return null
  return { ...context, hands, confidence: data.confidence, seed: data.validation_seed, exactCells: data.exact_cells, gameBounds: data.expected_controller_game_bounds[mode] }
}
export const precisionResearch = data
