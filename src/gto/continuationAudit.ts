import data from './continuationAuditData.json' with { type: 'json' }
export type AuditStage = 'vs_3bet' | 'vs_4bet'
export type AuditLevel = 'texture_flags' | 'texture_class_flags' | 'board_class_flags'
export type AuditModel = { texture_flags: { conditional_call_nashconv_bb: number }; texture_class_flags: { conditional_call_nashconv_bb: number }; board_class_flags: { conditional_call_nashconv_bb: number };
  by_seat: Record<string, Record<AuditLevel, { profile_root_bb: number; gain_root_bb: number }>>;
  future_street_envelope: { unresolved_showdown_probability: number; root_lower: number; root_upper: number } }
export type AuditData = { schema: string; formal_acceptance: number; normal_gto_admission: boolean; real_game_approximation_error: string; external_gto_comparison: string;
 condition: { players: number; stack_bb: number; ante_bb: number; rake_pct: number; raise_to_bb: number[] };
 population: { physical_flops: number; orbits: number; sampling_error: number };
 configs: Record<string, { root_call_probability: number; root_probability_error: number; models: Record<string, AuditModel> }> }
export const auditData = data as unknown as AuditData
export const auditModels = ['fixed_small', 'fixed_large', 'posterior_small', 'posterior_large', 'posterior_union'] as const
export const auditLevels: AuditLevel[] = ['texture_flags', 'texture_class_flags', 'board_class_flags']
export function findContinuationAudit(stage: string, preflop: string, source: unknown = auditData) {
 try {
  const d = source as AuditData
  if (!['vs_3bet', 'vs_4bet'].includes(stage) || !['learned_small', 'learned_large'].includes(preflop) || d.schema !== 'pokerid-continuation-audit-results-v1' || d.formal_acceptance !== 0 || d.normal_gto_admission !== false || d.real_game_approximation_error !== 'UNKNOWN' || d.external_gto_comparison !== 'NOT PERFORMED' || d.population.physical_flops !== 22100 || d.population.orbits !== 1755 || d.population.sampling_error !== 0) return null
  if (d.condition.players !== 2 || d.condition.stack_bb !== 50 || d.condition.ante_bb !== 0 || d.condition.rake_pct !== 0 || JSON.stringify(d.condition.raise_to_bb) !== '[2.5,9,21,50]') return null
  const c = d.configs[`${preflop}|${stage}`]
  if (!c || !(c.root_call_probability > 0 && c.root_call_probability <= 1) || !Number.isFinite(c.root_probability_error) || c.root_probability_error > 1e-10 || Object.keys(c.models).sort().join(',') !== [...auditModels].sort().join(',')) return null
  for (const model of Object.values(c.models)) {
   const ns = auditLevels.map(l => model[l].conditional_call_nashconv_bb)
   if (ns.some(x => !Number.isFinite(x) || x < -1e-8) || ns[1] + 1e-7 < ns[0] || ns[2] + 1e-7 < ns[1]) return null
   const e = model.future_street_envelope
   if (![e.root_lower, e.root_upper, e.unresolved_showdown_probability].every(Number.isFinite) || e.root_lower > e.root_upper || e.unresolved_showdown_probability < 0 || e.unresolved_showdown_probability > c.root_call_probability + 1e-8) return null
  }
  return c
 } catch { return null }
}
