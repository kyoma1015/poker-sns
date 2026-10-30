const TEST_URL = 'https://hbhyuotzginwysrineyo.supabase.co'
type Env = Record<string, unknown>
/** Configuration fence only. JWT, allowlist and RLS remain server authorities. */
export function assertVideoCloudTestClient(env: Env, origin?: string): void {
  const requested = env.VITE_VIDEO_CLOUD_TEST_ENABLED !== undefined ||
    env.VITE_VIDEO_CLOUD_TEST_ORIGIN !== undefined ||
    String(env.VITE_SUPABASE_URL ?? '').includes('hbhyuotzginwysrineyo')
  if (!requested) return
  const reject = () => { throw new Error('動画検証環境の接続設定が不正です。') }
  if (env.VITE_VIDEO_CLOUD_TEST_ENABLED !== 'true' || env.VITE_SUPABASE_URL !== TEST_URL) reject()
  if (env.PROD !== true || env.VITE_VIDEO_SERVER_ENABLED === 'true') reject()
  const configured = env.VITE_VIDEO_CLOUD_TEST_ORIGIN
  if (typeof configured !== 'string' || !origin || configured !== origin) reject()
  let url: URL
  try { url = new URL(String(configured)) } catch { return reject() }
  if (url.protocol !== 'https:' || url.origin !== configured ||
      !/^poker-id-video-test-[a-z0-9-]+\.vercel\.app$/.test(url.hostname)) reject()
  // Reject unexpected privileged env names even if accidentally made public.
  for (const key of Object.keys(env)) {
    if (/SERVICE_ROLE|SECRET_KEY|DATABASE_URL|DB_URL|ATTESTATION_KEY_HEX/.test(key) && env[key]) reject()
  }
}
export function assertCurrentVideoCloudTestClient(): void {
  assertVideoCloudTestClient(import.meta.env as unknown as Env,
    typeof location === 'undefined' ? undefined : location.origin)
}
