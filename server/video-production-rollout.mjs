const PRODUCTION_URL = 'https://ephptepeuespnxtzdqby.supabase.co'
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
export async function assertProductionVideoPublisher(viewer, userId) {
  const env = process.env
  if (env.VIDEO_PRODUCTION_LIMITED_ROLLOUT !== 'true' || env.VITE_SUPABASE_URL !== PRODUCTION_URL ||
      env.VIDEO_SERVER_ENABLED !== 'true' || !UUID.test(userId)) throw new Error('video rollout disabled')
  const allowed = (env.VIDEO_ALLOWED_USER_IDS || '').split(',')
  if (!allowed.length || allowed.some(id => !UUID.test(id)) || !allowed.includes(userId)) throw new Error('video user denied')
  const state = await viewer.rpc('video_rollout_allowed')
  if (state.error || state.data !== true) throw new Error('video database rollout disabled')
}
