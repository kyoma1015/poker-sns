import { supabase } from './supabase'

type NotificationType = 'like' | 'comment' | 'follow'

type RpcError = {
  code?: string
  message?: string
  status?: number
}

const MAX_ATTEMPTS = 3
const ATTEMPT_TIMEOUT_MS = 4500
const TOTAL_TIMEOUT_MS = 15000

// PostgREST returns the HTTP status beside "error", not inside it.
// Authorization and validation failures must never be retried.
function isTransientNotificationError(error: RpcError): boolean {
  if (error.status === 401 || error.status === 403) return false
  if (error.code === '42501' || error.code === '22023') return false

  if (typeof error.status === 'number') {
    if (error.status === 429 || error.status >= 500) return true
    if (error.status >= 400) return false
  }

  const code = error.code ?? ''
  if (code.startsWith('08') || code === '57014' ||
      code === 'PGRST000' || code === 'PGRST001' || code === 'PGRST002') {
    return true
  }

  return /(?:failed to fetch|networkerror|network request failed|fetch failed|timeout|timed out)/i
    .test(error.message ?? '')
}

function normalizeThrownError(error: unknown): RpcError {
  if (error instanceof Error) {
    const extended = error as Error & { code?: string; status?: number }
    return { message: extended.message, code: extended.code, status: extended.status }
  }
  return { message: String(error) }
}

// Each attempt has a hard deadline. Three attempts plus the two delays
// fit within the total budget, even when every request hangs.
export async function createVerifiedNotification(
  eventType: NotificationType,
  eventId: string,
): Promise<RpcError | null> {
  const deadline = Date.now() + TOTAL_TIMEOUT_MS

  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    const remaining = deadline - Date.now()
    if (remaining <= 0) {
      return { message: '通知の送信がタイムアウトしました' }
    }

    const controller = new AbortController()
    const timeoutFailure: RpcError = {
      message: '通知RPCがタイムアウトしました',
      code: 'NOTIFICATION_TIMEOUT',
    }
    let timer: ReturnType<typeof setTimeout> | undefined

    // Promise.race guarantees a deadline even if a transport ignores abort.
    // The in-flight request is also aborted; event_key makes retry idempotent.
    const request = (async (): Promise<RpcError | null> => {
      try {
        const { error, status } = await supabase
          .rpc('create_verified_notification', {
            p_event_type: eventType,
            p_event_id: eventId,
          })
          .abortSignal(controller.signal)
        return error
          ? { code: error.code, message: error.message, status }
          : null
      } catch (error) {
        return normalizeThrownError(error)
      }
    })()

    const timeout = new Promise<RpcError>(resolve => {
      timer = setTimeout(() => {
        controller.abort()
        resolve(timeoutFailure)
      }, Math.min(ATTEMPT_TIMEOUT_MS, remaining))
    })

    const failure = await Promise.race([request, timeout])
    if (timer !== undefined) clearTimeout(timer)
    if (failure === null) return null

    if (attempt === MAX_ATTEMPTS - 1) return failure
    if (failure.code !== 'NOTIFICATION_TIMEOUT' && !isTransientNotificationError(failure)) return failure

    const delay = Math.min(300 * (2 ** attempt), Math.max(0, deadline - Date.now()))
    if (delay <= 0) return failure
    await new Promise<void>(resolve => setTimeout(resolve, delay))
  }

  return { message: '通知の送信結果を確認できませんでした' }
}
