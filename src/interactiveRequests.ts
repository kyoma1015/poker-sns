type Poll = {
  post_id: string
  kind: 'poll' | 'question'
  options: string[]
  closes_at: string | null
  is_anonymous: boolean
}

// Revalidate at click time: a card can remain open past its closing time.
export function pollVoteRequest(item: Poll, choice: number | null, now = Date.now()) {
  if (!item || item.kind !== 'poll' || !Array.isArray(item.options) ||
      item.options.length < 2 || item.options.length > 4 ||
      typeof item.is_anonymous !== 'boolean' ||
      !Number.isInteger(choice) || choice === null ||
      choice < 0 || choice >= item.options.length) {
    throw new Error('投票する選択肢を選び直してください。')
  }
  const deadline = item.closes_at ? Date.parse(item.closes_at) : NaN
  if (!Number.isFinite(deadline) || !Number.isFinite(now) || deadline <= now) {
    throw new Error('投票期限が終了しているか、期限を確認できません。再読み込みしてください。')
  }
  return {
    p_post_id: item.post_id,
    p_option_index: choice,
    p_answer: null,
    p_is_anonymous: item.is_anonymous,
  }
}

// Reject stale/forged question mode at the RPC boundary, not just in the UI.
export function createPollRequest(mode: string, content: string, options: string[], hours: number, anonymous: boolean) {
  if (mode !== 'poll') throw new Error('作成できるのはアンケートのみです。')
  if (typeof content !== 'string' || !Array.isArray(options) ||
      options.some(option => typeof option !== 'string')) {
    throw new Error('アンケートの内容・選択肢・期限を確認してください。')
  }
  const normalized = options.map(option => option.trim())
  if (!content.trim() || content.trim().length > 500 || normalized.length < 2 || normalized.length > 4 ||
      normalized.some(option => !option || option.length > 80) ||
      new Set(normalized.map(option => option.toLowerCase())).size !== normalized.length ||
      ![1, 6, 24, 72, 168].includes(hours) || typeof anonymous !== 'boolean') {
    throw new Error('アンケートの内容・選択肢・期限を確認してください。')
  }
  return { p_content: content.trim(), p_kind: 'poll' as const, p_options: normalized,
    p_hours: hours, p_is_anonymous: anonymous, p_question_policy: null }
}

// Defense in depth only. Server-side RPC/RLS anonymity still needs isolated DB QA.
export function pollDisplayResult<T extends { voters: unknown[]; answers: unknown[] }>(anonymous: boolean, result: T): T {
  return anonymous ? { ...result, voters: [], answers: [] } : result
}
