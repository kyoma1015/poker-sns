import { supabase } from './supabase'

type NotificationType = 'like' | 'comment' | 'follow'

type RpcError = {
  code?: string
  message?: string
  status?: number
}

// Only retry transient transport/server failures. The RPC is idempotent for
// a given event ID; invalid input, permission and policy errors are not retried.
function isTransientNotificationError(error: RpcError): boolean {
  if (typeof error.status === 'number') return error.status >= 500 || error.status === 429
  const code = error.code ?? ''
  if (code.startsWith('08') || code === '57014' || code === 'PGRST000' || code === 'PGRST001' || code === 'PGRST002') return true
  return /(?:failed to fetch|networkerror|network request failed|fetch failed|timeout|timed out)/i.test(error.message ?? '')
}

export async function createVerifiedNotification(
  eventType: NotificationType,
  eventId: string,
): Promise<RpcError | null> {
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const { error } = await supabase.rpc('create_verified_notification', {
        p_event_type: eventType,
        p_event_id: eventId,
      })
      if (!error) return null
      if (attempt === 2 || !isTransientNotificationError(error)) return error
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error)
      const wrapped = { message }
      if (attempt === 2 || !isTransientNotificationError(wrapped)) return wrapped
    }
    await new Promise(resolve => setTimeout(resolve, 300 * (2 ** attempt)))
  }
  return { message: '通知の送信結果を確認できませんでした' }
}
