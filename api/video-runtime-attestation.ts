import type { VercelRequest, VercelResponse } from '@vercel/node'
import { spawn } from 'node:child_process'
import { isAbsolute, join } from 'node:path'

/**
 * Read-only runtime attestation for preview deployments only.
 * Does not accept user input as a command, and never returns filesystem paths.
 */
export default async function handler(req: VercelRequest, res: VercelResponse) {
  res.setHeader('Cache-Control', 'no-store')
  res.setHeader('X-Content-Type-Options', 'nosniff')
  if (process.env.VERCEL_ENV !== 'preview') return res.status(404).end()
  if (req.method !== 'GET') return res.status(405).end()
  const path = process.env.FFPROBE_BINARY_PATH || join(process.cwd(), 'api', 'bin', 'ffprobe')
  if (!path || !isAbsolute(path)) return res.status(503).json({ ffprobe: 'unconfigured' })
  const result = await new Promise<boolean>(resolve => {
    let settled = false
    const done = (ok: boolean) => { if (!settled) { settled = true; clearTimeout(timer); resolve(ok) } }
    const child = spawn(path, ['-version'], { shell: false, stdio: 'ignore' })
    const timer = setTimeout(() => { child.kill(); done(false) }, 5000)
    child.on('error', () => done(false))
    child.on('close', code => done(code === 0))
  })
  return res.status(result ? 200 : 503).json({ ffprobe: result ? 'executable' : 'unavailable' })
}
