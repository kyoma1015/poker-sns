type ShareTransport = {
  share?: (data: ShareData) => Promise<void>
  clipboard?: { writeText: (text: string) => Promise<void> }
}

// Cancellation is expected on mobile. Never turn it into an error or copy a
// link unexpectedly; other native-share failures can use the clipboard fallback.
export async function sharePost(data: { title: string; text: string; url: string }, transport: ShareTransport): Promise<'shared' | 'copied' | 'cancelled'> {
  if (transport.share) {
    try {
      await transport.share(data)
      return 'shared'
    } catch (error) {
      if (typeof error === 'object' && error !== null && 'name' in error && error.name === 'AbortError') return 'cancelled'
    }
  }
  if (!transport.clipboard) throw new Error('共有を利用できません。投稿を開いてURLをコピーしてください。')
  try {
    await transport.clipboard.writeText(data.url)
    return 'copied'
  } catch {
    throw new Error('リンクをコピーできませんでした。投稿を開いてURLをコピーしてください。')
  }
}
