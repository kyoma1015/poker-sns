import data from './abstractResearchData.json' with { type: 'json' }
import { canonicalQuery, handLabels } from './rangeCatalog.ts'
import type { RangeQuery } from './rangeCatalog.ts'

export const abstractResearch = data
export const abstractResearchQuery: RangeQuery = { format: 'mtt', players: 2, seat: 0, stackBb: '50', anteBb: '0',
  rakePct: '0', rakeCapBb: null, openBb: '2.5', threeBetBb: '9', fourBetBb: '21', stage: 'rfi' }
export type AbstractStage = 'rfi' | 'vs_open' | 'vs_3bet' | 'vs_4bet'
export function findAbstractResearch(value: unknown): AbstractStage | null {
  let q: RangeQuery
  try { q = canonicalQuery(value) } catch { return null }
  if (!['rfi', 'vs_open', 'vs_3bet', 'vs_4bet'].includes(q.stage) || data.full_game_gto_verified !== false ||
    data.schema !== 'pokerid-research-preflop-abstraction-v1' || q.players !== 2 || q.stackBb !== '50' ||
    q.anteBb !== '0' || q.rakePct !== '0' || q.rakeCapBb !== null || q.openBb !== '2.5' || q.threeBetBb !== '9' || q.fourBetBb !== '21') return null
  const stage = q.stage as AbstractStage
  for (const model of Object.values(data.models)) {
    const context = model.contexts[stage]
    if (context.actor !== q.seat || context.coverage !== 169 || Object.keys(context.hands).length !== 169 ||
      !Number.isFinite(model.abstract_nashconv_bb) || model.abstract_nashconv_bb < 0 || model.abstract_nashconv_bb > .01) return null
    const hands = context.hands as Record<string, { frequencies: number[]; ev_bb: number; model_ev_interval_bb: number[] }>
    if (!handLabels.every(label => {
      const row = hands[label]
      return row && row.frequencies.length === context.actions.length && row.frequencies.every(x => Number.isFinite(x) && x >= 0) &&
        Math.abs(row.frequencies.reduce((a, b) => a + b, 0) - 1) < 1e-9 && Number.isFinite(row.ev_bb) &&
        row.model_ev_interval_bb.length === 2 && row.model_ev_interval_bb.every(Number.isFinite) &&
        row.model_ev_interval_bb[0] <= row.ev_bb && row.ev_bb <= row.model_ev_interval_bb[1]
    })) return null
  }
  return stage
}
