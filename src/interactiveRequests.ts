type Poll = {
  post_id: string
  kind: 'poll' | 'question'
  options: string[]
  closes_at: string | null
  is_anonymous: boolean
}

// Revalidate at click time: a card can remain open past its closing time.
export function pollVoteRequest(item: Poll, choice: number | null, now = Date.now()) {
  if (item.kind !== 'poll' || !Number.isInteger(choice) || choice === null ||
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
