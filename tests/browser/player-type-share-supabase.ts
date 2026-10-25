import fixture from '../fixtures/player-type-v2.json'
// Fixture transport only. The actual SDK/credentials are never imported.
export const supabase = {
  auth: { getUser: async () => ({ data: { user: { id: 'qa-owner' } }, error: null }) },
  rpc: async (name: string, args?: { p_result_id?: string }) => {
    if (name === 'get_player_type_v2_questions') return { data: fixture.rows, error: null }
    if (name === 'is_my_player_type_v2_result') return { data: true, error: null }
    if (name === 'get_player_type_v2_result_detail') return { data: [{ result_id: args?.p_result_id || 'qa-result', result_type_key: 'lion', animal_name_ja: args?.p_result_id === 'qa-next' ? 'QA次のライオン' : 'QAライオン', catchphrase: '合成の表示確認', core_answer_count: 50, description: 'QA description', trait_scores: {}, discriminator_scores: {}, behavior_text: 'QA', strength_text: 'QA', weakness_text: 'QA', perceived_text: 'QA', best_situation_text: 'QA' }], error: null }
    return { data: [], error: null }
  },
}
