import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from './supabase'

type ReportStatus = 'pending' | 'in_progress' | 'reviewed' | 'dismissed'
type Report = {
  id: string
  post_id: string
  reporter_id: string
  reason: string
  details: string | null
  status: ReportStatus
  created_at: string
  post_content: string | null
  post_author_id: string | null
  author_name: string | null
  author_poker_id: string | null
  reporter_poker_id: string | null
}

const statuses: { value: ReportStatus; label: string }[] = [
  { value: 'pending', label: '未対応' },
  { value: 'in_progress', label: '対応中' },
  { value: 'reviewed', label: '対応済み' },
  { value: 'dismissed', label: '却下' },
]
const reasons: Record<string, string> = {
  spam: 'スパム', harassment: '嫌がらせ',
  inappropriate: '不適切な内容', other: 'その他',
}

export default function AdminReports() {
  const navigate = useNavigate()
  const [authorized, setAuthorized] = useState(false)
  const [loading, setLoading] = useState(true)
  const [reports, setReports] = useState<Report[]>([])
  const [filter, setFilter] = useState('all')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState<string | null>(null)

  const loadReports = useCallback(async () => {
    setMessage('')
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) {
      setAuthorized(false)
      setLoading(false)
      navigate('/login')
      return
    }
    const { data: isAdmin, error: authError } = await supabase.rpc('poker_id_is_admin')
    if (authError || isAdmin !== true) {
      setAuthorized(false)
      setLoading(false)
      setMessage(authError ? `権限確認エラー: ${authError.message}` : 'この画面は運営専用です。')
      return
    }
    setAuthorized(true)
    const { data, error } = await supabase.rpc('poker_id_admin_list_reports')
    if (error) setMessage(`通報の取得に失敗しました: ${error.message}`)
    else setReports(Array.isArray(data) ? data as Report[] : [])
    setLoading(false)
  }, [navigate])

  useEffect(() => { void loadReports() }, [loadReports])

  const updateStatus = async (reportId: string, status: ReportStatus) => {
    setSaving(reportId)
    setMessage('')
    const { error } = await supabase.rpc('poker_id_admin_update_report_status', {
      p_report_id: reportId, p_status: status,
    })
    if (error) setMessage(`更新に失敗しました: ${error.message}`)
    else setReports(current => current.map(report =>
      report.id === reportId ? { ...report, status } : report
    ))
    setSaving(null)
  }

  const visible = reports.filter(r => filter === 'all' || r.status === filter)
  const panel: React.CSSProperties = {
    background: '#191919', border: '1px solid #383838', borderRadius: 12,
    padding: 16, marginBottom: 14, textAlign: 'left',
  }
  const muted: React.CSSProperties = { color: '#aaa', fontSize: 13 }

  return (
    <main className="app">
      <div className="card" style={{ maxWidth: 780, width: '100%', boxSizing: 'border-box' }}>
        <h1 className="logo">Poker ID</h1>
        <p className="subtitle">運営・通報管理</p>
        {loading && <p>読み込み中...</p>}
        {message && <p role="alert" style={{ color: '#f0b4b4' }}>{message}</p>}
        {authorized && !loading && <>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 18 }}>
            <button style={{ width: 'auto' }} onClick={() => void loadReports()}>更新</button>
            <select aria-label="通報の状態で絞り込み" value={filter} onChange={e => setFilter(e.target.value)}
              style={{ padding: 10, background: '#242424', color: '#fff', border: '1px solid #555', borderRadius: 8 }}>
              <option value="all">すべて（{reports.length}件）</option>
              {statuses.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
          <p style={muted}>直近200件まで表示・新しい順</p>
          {visible.length === 0 && <p>該当する通報はありません。</p>}
          {visible.map(report => <div key={report.id} style={panel}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
              <strong>{reasons[report.reason] ?? report.reason}</strong>
              <span style={muted}>{new Date(report.created_at).toLocaleString('ja-JP')}</span>
            </div>
            <p style={{ ...muted, marginTop: 10 }}>通報者: @{report.reporter_poker_id || '不明'} ／ 投稿者: @{report.author_poker_id || '不明'}</p>
            <p style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', marginTop: 10 }}>
              {report.details || '追加説明なし'}
            </p>
            <div style={{ borderLeft: '3px solid #555', paddingLeft: 12, margin: '14px 0' }}>
              <span style={muted}>対象投稿</span>
              <p style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', margin: '6px 0' }}>
                {report.post_content || '（本文なし・画像のみの投稿など）'}
              </p>
              <button style={{ width: 'auto', padding: '6px 12px' }} onClick={() => navigate(`/post/${report.post_id}`)}>
                投稿を開く
              </button>
            </div>
            <label style={{ display: 'block', ...muted, marginBottom: 6 }} htmlFor={`status-${report.id}`}>対応状況</label>
            <select id={`status-${report.id}`} value={report.status} disabled={saving === report.id}
              onChange={e => void updateStatus(report.id, e.target.value as ReportStatus)}
              style={{ padding: 10, width: '100%', maxWidth: 230, background: '#242424', color: '#fff', border: '1px solid #555', borderRadius: 8 }}>
              {statuses.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>)}
        </>}
        <button className="signup-button" onClick={() => navigate('/timeline')} style={{ marginTop: 20 }}>
          タイムラインへ戻る
        </button>
      </div>
    </main>
  )
}
