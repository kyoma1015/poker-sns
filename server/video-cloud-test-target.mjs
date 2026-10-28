// This guard grants no publication authority; callers must still enforce JWT/RLS.
export const CLOUD_TEST_REF = 'hbhyuotzginwysrineyo'
export const CLOUD_TEST_URL = 'https://' + CLOUD_TEST_REF + '.supabase.co'
export function assertCloudTestTarget(env) {
  const fail = () => { throw new Error('cloud video test configuration rejected') }
  if (env.VIDEO_CLOUD_TEST_ENABLED !== 'true' || env.VERCEL_ENV !== 'preview') fail()
  if (env.VIDEO_CLOUD_TEST_PROJECT_REF !== CLOUD_TEST_REF) fail()
  if (env.VITE_SUPABASE_URL !== CLOUD_TEST_URL || env.SUPABASE_URL !== CLOUD_TEST_URL) fail()
  if (!env.VIDEO_CLOUD_TEST_VERCEL_PROJECT_ID || env.VERCEL_PROJECT_ID !== env.VIDEO_CLOUD_TEST_VERCEL_PROJECT_ID ||
      env.VERCEL_PROJECT_ID === 'prj_XfvN7NTO8lo6xXcjHZWGTUIp4VBI') fail()
  if (env.VIDEO_PRODUCTION_FENCED_READY === 'true' || env.VIDEO_ATTESTED_RPC_RELEASE_APPROVED === 'true') fail()
  // Cloud test handlers must never inherit privileged production or QA clients.
  for (const key of ['SUPABASE_SERVICE_ROLE_KEY','SUPABASE_SECRET_KEY','SUPABASE_DB_URL','DATABASE_URL','VIDEO_QA_ENV']) {
    if (env[key]) fail()
  }
  return Object.freeze({ projectRef: CLOUD_TEST_REF, url: CLOUD_TEST_URL })
}

/** Fail before I/O when cloud testing is requested or a test endpoint is present.
 * This does not enable publication; existing release gates remain mandatory.
 */
export function assertCloudTestRequestConfiguration(env) {
  const testHost = CLOUD_TEST_REF + '.supabase.co'
  const requested = env.VIDEO_CLOUD_TEST_ENABLED !== undefined ||
    env.VIDEO_CLOUD_TEST_PROJECT_REF !== undefined ||
    env.VIDEO_CLOUD_TEST_VERCEL_PROJECT_ID !== undefined ||
    [env.VITE_SUPABASE_URL, env.SUPABASE_URL].some(value =>
      typeof value === 'string' && value.includes(testHost))
  if (requested) return assertCloudTestTarget(env)
  return null
}
