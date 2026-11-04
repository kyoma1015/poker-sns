// Client DTO validation only. Database authorization still requires authentic RLS.
export type DirectMessage = {
 id: string
 sender_id: string
 receiver_id: string
 content: string
 created_at: string
 read_at: string | null
}
const timestamp = (value: unknown): value is string =>
 typeof value === 'string' && Number.isFinite(Date.parse(value))

export function isDirectMessageForConversation(
 value: unknown, accountId: string, peerId: string | undefined,
): value is DirectMessage {
 if (!value || typeof value !== 'object' || Array.isArray(value) || !accountId || !peerId) return false
 const row = value as Record<string, unknown>
 if (!['id','sender_id','receiver_id','content','created_at','read_at'].every(key=>Object.hasOwn(row,key))) return false
 if (typeof row.id !== 'string' || !row.id.trim() || typeof row.content !== 'string' ||
   !timestamp(row.created_at) || !(row.read_at === null || timestamp(row.read_at))) return false
 return (row.sender_id === accountId && row.receiver_id === peerId) ||
   (row.sender_id === peerId && row.receiver_id === accountId)
}

export function conversationMessages(value: unknown, accountId: string, peerId: string | undefined): DirectMessage[] {
 // Null is the existing empty-result convention; non-array payloads are failures.
 if (value === null) return []
 if (!Array.isArray(value)) throw new Error('Invalid conversation response')
 return value.filter((row): row is DirectMessage => isDirectMessageForConversation(row,accountId,peerId))
}
