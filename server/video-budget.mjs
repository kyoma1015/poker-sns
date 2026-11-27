import { createClient } from '@supabase/supabase-js'

export function videoBudgetRequired() {
  return process.env.VIDEO_USAGE_BUDGET_ENABLED === 'true' ||
    (process.env.VIDEO_GENERAL_PUBLIC_RELEASE_APPROVED === 'true' &&
     process.env.VIDEO_PUBLIC_ROLLOUT_ENABLED === 'true')
}

let readerSession

async function loginReader(url, anon, email, password) {
  const reader = createClient(url, anon, { auth: { persistSession: false, autoRefreshToken: false } })
  const { data, error } = await reader.auth.signInWithPassword({ email, password })
  if (error || !data.session?.expires_at) throw new Error('video reader unavailable')
  return { token: data.session.access_token, expiresAt: data.session.expires_at }
}

export async function videoBudgetCredential(
  viewer, url, anon, viewerAuthorization,
  operation,
){
  if (!videoBudgetRequired()) return viewerAuthorization
  const key = process.env.VIDEO_USAGE_METER_KEY
  const email = process.env.VIDEO_STORAGE_READER_EMAIL
  const password = process.env.VIDEO_STORAGE_READER_PASSWORD
  if (!key || !/^[0-9a-f]{64}$/.test(key) || !email || !password) throw new Error('video budget unavailable')
  const result = await viewer.rpc('video_meter_operation', { p_operation: operation, p_key: key })
  if (result.error || result.data !== true) throw new Error('video budget exhausted or stopped')
  const cached = readerSession
  if (cached && (await cached).expiresAt <= Math.floor(Date.now() / 1000) + 60 && readerSession === cached) {
    readerSession = undefined
  }
  readerSession ??= loginReader(url, anon, email, password).catch(error => {
    readerSession = undefined
    throw error
  })
  return 'Bearer ' + (await readerSession).token
}
