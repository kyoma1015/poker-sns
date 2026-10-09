import { useNavigate } from 'react-router-dom'

type Tool = { icon: string; title: string; description: string; path?: string }

const available: Tool[] = [
  { icon: '♠', title: 'TDAクイズ', description: 'ルールをクイズで学習', path: '/tda' },
  { icon: '⌕', title: 'TDA検索', description: 'ルール・裁定を調べる', path: '/tda' },
  { icon: '▥', title: '実戦記録', description: '成績・収支を管理', path: '/results' },
  { icon: '🐾', title: 'プレイスタイル診断', description: '36種類の動物で分析', path: '/player-type' },
]

const upcoming: Tool[] = [
  { icon: '％', title: 'ポットオッズ計算', description: 'コールに必要な勝率' },
  { icon: '◈', title: 'エクイティ計算', description: 'ハンドの勝率を分析' },
  { icon: '◎', title: 'ブラフEV計算', description: 'ブラフに必要な成功率' },
  { icon: '♧', title: 'ハンド分析', description: 'プレイした局面を振り返る' },
]

function ToolCard({ tool }: { tool: Tool }) {
  const navigate = useNavigate()
  const enabled = Boolean(tool.path)
  return (
    <button
      type="button"
      disabled={!enabled}
      onClick={() => tool.path && navigate(tool.path)}
      style={{
        width: '100%', minWidth: 0, minHeight: 132, padding: '17px 13px',
        display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 8,
        textAlign: 'left', borderRadius: 14,
        border: `1px solid ${enabled ? '#343434' : '#292929'}`,
        background: enabled ? '#191919' : '#141414',
        color: enabled ? '#fff' : '#bcbcbc',
        cursor: enabled ? 'pointer' : 'default', opacity: 1,
      }}
    >
      <span aria-hidden="true" style={{ fontSize: 24, lineHeight: 1.1, color: enabled ? '#fff' : '#888' }}>{tool.icon}</span>
      <span style={{ fontSize: 13, fontWeight: 800, lineHeight: 1.4 }}>{tool.title}</span>
      <span style={{ fontSize: 11, color: '#999', lineHeight: 1.5 }}>{tool.description}</span>
      {!enabled && <span style={{ fontSize: 10, color: '#aaa', border: '1px solid #3b3b3b', borderRadius: 20, padding: '3px 8px' }}>開発予定</span>}
    </button>
  )
}

function PokerTools() {
  const navigate = useNavigate()
  return (
    <main className="app" style={{ paddingBottom: 90 }}>
      <div className="card" style={{ paddingTop: 18 }}>
        <button type="button" onClick={() => navigate('/timeline')} style={{ width: 'auto', padding: '3px 0', background: 'transparent', color: '#aaa', fontSize: 13, marginBottom: 17 }}>← ホームに戻る</button>
        <h1 style={{ fontSize: 24, fontWeight: 900, margin: '0 0 8px' }}>♠ ポーカーツール</h1>
        <p style={{ color: '#999', fontSize: 13, lineHeight: 1.6, margin: '0 0 25px' }}>ポーカーをもっと楽しく、もっと便利に。</p>
        <h2 style={{ fontSize: 15, margin: '0 0 12px' }}>利用できるツール</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 10 }}>
          {available.map(tool => <ToolCard key={tool.title} tool={tool} />)}
        </div>
        <div style={{ borderTop: '1px solid #303030', margin: '28px 0 22px' }} />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, marginBottom: 13 }}>
          <h2 style={{ fontSize: 15, margin: 0 }}>今後追加予定</h2>
          <span style={{ fontSize: 10, letterSpacing: 1, color: '#999' }}>COMING SOON</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 10 }}>
          {upcoming.map(tool => <ToolCard key={tool.title} tool={tool} />)}
        </div>
        <p style={{ fontSize: 11, color: '#777', lineHeight: 1.6, marginTop: 18 }}>※ 開発予定の機能は現在利用できません。提供時期は未定です。</p>
      </div>
    </main>
  )
}

export default PokerTools
