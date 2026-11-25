// Keep a visible status even when an imported module fails during initialization.
async function start() {
  const status = document.getElementById('startup-status')
  const configured = import.meta.env.VITE_VIDEO_CLOUD_TEST_ORIGIN
  if (import.meta.env.VITE_VIDEO_CLOUD_TEST_ENABLED === 'true' &&
      typeof configured === 'string' &&
      /^https:\/\/poker-id-video-test-[a-z0-9-]+\.vercel\.app$/.test(configured) &&
      location.origin !== configured) {
    if (status) {
      const link = document.createElement('a')
      link.href = configured
      link.textContent = '動画検証用の固定URLを開く'
      link.style.color = '#93c5fd'
      status.replaceChildren('このURLでは検証環境を起動できません。', document.createElement('br'), link)
    }
    return
  }

  try {
    await import('./main')
  } catch {
    if (status) status.textContent = 'Poker IDを読み込めませんでした。ページを再読み込みしてください。'
  }
}

void start()
