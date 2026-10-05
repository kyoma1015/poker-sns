import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from './supabase'

function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const navigate = useNavigate()

  const handleLogin = async () => {
    setMessage('ログイン中...')

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      setMessage(`エラー：${error.message}`)
      return
    }

    navigate('/home')
  }

  return (
    <main className="app">
      <div className="card">
        <h1 className="logo">Poker ID</h1>
        <p className="subtitle">ログイン</p>

        <div className="buttons">
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
            onClick={handleLogin}
          >
            ログイン
          </button>

          {message && <p>{message}</p>}
        </div>
      </div>
    </main>
  )
}

export default Login