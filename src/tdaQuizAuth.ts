type AuthIssue = { code?: string; name?: string; status?: number }
type AuthReader = {
  getSession(): Promise<{ data: { session: unknown }; error: AuthIssue | null }>
  getUser(): Promise<{ data: { user: unknown }; error: AuthIssue | null }>
}
type QuizAuthResult = { ok: true } | { ok: false; requiresLogin: boolean; message: string }

const retry = (): QuizAuthResult => ({
  ok: false, requiresLogin: false,
  message: 'ログイン状態を確認できませんでした。通信状況を確認して再度お試しください。',
})
const login = (): QuizAuthResult => ({
  ok: false, requiresLogin: true,
  message: '回答を記録するにはログインしてください。有効期限が切れている場合は再度ログインしてください。',
})
function expired(error: AuthIssue) {
  return error.status === 401 || error.name === 'AuthSessionMissingError' ||
    ['session_not_found', 'refresh_token_not_found', 'refresh_token_already_used', 'bad_jwt', 'user_not_found']
      .includes(error.code ?? '')
}

// A transport failure is not evidence that the user's login expired.
export async function checkQuizAuthentication(auth: AuthReader): Promise<QuizAuthResult> {
  try {
    const session = await auth.getSession()
    if (session.error) return expired(session.error) ? login() : retry()
    if (!session.data.session) return login()
    const user = await auth.getUser()
    if (user.error) return expired(user.error) ? login() : retry()
    return user.data.user ? { ok: true } : login()
  } catch {
    return retry()
  }
}
