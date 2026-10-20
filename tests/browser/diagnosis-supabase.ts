import fixture from '../fixtures/player-type-v2.json'
const calls: { name: string; args: unknown }[] = []
const controls = { failSave: false, pendingSave: false, rejectSave: null as null | (() => void), pendingShare: false, resolveShare: null as null | (() => void) }
Object.assign(window, { diagnosisCalls: calls, diagnosisControls: controls })
function detail(id: string) {
  return { result_id: id, result_type_key: id === 'two' ? 'tiger' : 'lion', animal_name_ja: id === 'two' ? 'トラ' : 'ライオン',
    catchphrase: 'テスト用の傾向です', confidence: 0.7, top_margin: 0.1, core_answer_count: 50, is_public: true, completed_at: '2026-10-20T00:00:00Z',
    animal_name_en: 'test', description: '判断の傾向を表示します', behavior_text: '場面に応じた行動', strength_text: '自分の基準', weakness_text: '偏りに注意',
    perceived_text: '行動の傾向', best_situation_text: '落ち着いた場面', trait_scores: { initiative: 12, confidence: 6, patience: 10 }, discriminator_scores: {} }
}
export const supabase = {
  auth: { getUser: async () => ({ data: { user: { id: 'qa-user' } }, error: null }) },
  rpc: async (name: string, args?: { p_result_id?: string }) => {
    calls.push({ name, args })
    if (name === 'get_player_type_v2_questions') return { data: fixture.rows, error: null }
    if (name === 'get_player_type_v2_result_detail') return { data: [detail(args?.p_result_id || 'one')], error: null }
    if (name === 'is_my_player_type_v2_result') return { data: args?.p_result_id !== 'visitor', error: null }
    if (name === 'complete_player_type_v2_diagnosis') {
      if (controls.pendingSave) await new Promise((_, reject) => { controls.rejectSave = () => reject(new Error('late-save-failure')) })
      if (controls.failSave) return { data: null, error: { message: 'test retry' } }
      return { data: [detail('one')], error: null }
    }
    throw new Error(`Unexpected test RPC ${name}`)
  },
  from: (name: string) => ({ insert: async (args: unknown) => {
    calls.push({ name: `${name}.insert`, args })
    if (controls.pendingShare) await new Promise<void>(resolve => { controls.resolveShare = resolve })
    return { error: null }
  } }),
}
