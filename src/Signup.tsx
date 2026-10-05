import { useState } from 'react'
import { supabase } from './supabase'

function Signup() {
  const [pokerId, setPokerId] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')

  const handleSignup = async () => {
    setMessage('登録中...')

    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          poker_id: pokerId,
          display_name: displayName,
        },
      },
    })

    if (error) {
      setMessage(`エラー：${error.message}`)
      return
    }

    setMessage('登録できました！メールを確認してください。')
  }

  return (
    <main className="app">
      <div className="card">
        <h1 className="logo">Poker ID</h1>
        <p className="subtitle">新規登録</p>

        <div className="buttons">
          <input
            type="text"
            placeholder="Poker ID"
            value={pokerId}
            onChange={(e) => setPokerId(e.target.value)}
          />

          <input
            type="text"
            placeholder="表示名"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />

          <input
            type="email"
            placeholder="メールアドレス"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <input
            type="password"
            placeholder="パスワード"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <button
            className="login-button"
            onClick={handleSignup}
          >
            アカウントを作成
          </button>

          {message && <p>{message}</p>}
        </div>
      </div>
    </main>
  )
}

export default Signup