const PRODUCTION_URL = 'https://ephptepeuespnxtzdqby.supabase.co'
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
export function assertProductionVideoConfiguration() {
  if (process.env.VIDEO_PRODUCTION_LIMITED_ROLLOUT !== 'true' || process.env.VITE_SUPABASE_URL !== PRODUCTION_URL) throw new Error('production video target disabled')
}
async function assertIdentity(viewer, userId, rpc) {
  assertProductionVideoConfiguration()
  const env = process.env
  if (env.VIDEO_PRODUCTION_LIMITED_ROLLOUT !== 'true' || env.VITE_SUPABASE_URL !== PRODUCTION_URL ||
      !UUID.test(userId)) throw new Error('video rollout disabled')
  // Public rollout requires TWO independent server-side flags and a positive
  // user-JWT-scoped database decision. Never infer public access from an
  // empty allowlist or from the client-side VITE feature flag.
  const generalPublic = env.VIDEO_GENERAL_PUBLIC_RELEASE_APPROVED === 'true' &&
    env.VIDEO_PUBLIC_ROLLOUT_ENABLED === 'true'
  if (!generalPublic) {
    const allowed = (env.VIDEO_ALLOWED_USER_IDS || '').split(',')
    if (!allowed.length || allowed.some(id => !UUID.test(id)) || !allowed.includes(userId)) {
      throw new Error('video user denied')
    }
  }
  const state = await viewer.rpc(rpc)
  if (state.error || state.data !== true) throw new Error('video database rollout disabled')
}

// A publication stop must not prevent an authorized owner from hiding a video.
export async function assertProductionVideoMember(viewer, userId) { return assertIdentity(viewer, userId, 'video_rollout_member') }
export async function assertProductionVideoPublisher(viewer, userId) {
  if (process.env.VIDEO_SERVER_ENABLED !== 'true') throw new Error('video rollout disabled')
  return assertIdentity(viewer, userId, 'video_rollout_allowed')
}
