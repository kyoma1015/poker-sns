import type { CSSProperties } from 'react'

export type PokerProfileExtrasData = {
  poker_started_year?: number | null
  poker_started_month?: number | null
  poker_years?: number | null
  main_play?: string | null
  poker_frequency?: string | null
  hobbies?: string[] | null
  poker_meaning?: string | null
  poker_meaning_detail?: string | null
  my_hand_cards?: string[] | null
  my_hand_reason?: string | null
}

export const POKER_FREQUENCIES: Record<string, string> = {
  less_than_monthly: '月1回未満', monthly_1_3: '月1〜3回', weekly_1: '週1回程度',
  weekly_2_3: '週2〜3回', weekly_4_plus: '週4回以上',
}
export const MAIN_PLAY_LABELS: Record<string, string> = {
  ring: 'リング派', tournament: 'トーナメント派', undecided: '決められない',
  cash: '決められない', balanced: '決められない',
}
export const HOBBY_PRESETS = [
  'ゲーム', 'アニメ', '漫画', '映画', 'ドラマ', '音楽', 'ライブ', 'カラオケ', '読書',
  '旅行', '国内旅行', '海外旅行', '温泉', 'サウナ', 'キャンプ', 'アウトドア', '登山',
  '釣り', 'ドライブ', 'ツーリング', '車', 'バイク', '自転車', '散歩',
  'グルメ', 'カフェ巡り', '料理', 'お菓子作り', 'お酒', 'コーヒー',
  '筋トレ', 'ランニング', 'ウォーキング', 'ヨガ', 'ジム', 'サッカー', 'フットサル',
  '野球', 'バスケ', 'テニス', 'バドミントン', '卓球', 'ゴルフ', 'ボウリング',
  'ダーツ', 'ビリヤード', 'スノーボード', 'スキー', 'サーフィン', '水泳',
  '写真', 'カメラ', '動画制作', '動画鑑賞', 'イラスト', 'デザイン', 'ファッション',
  '美容', 'コスメ', 'インテリア', 'DIY', 'ガジェット', 'プログラミング',
  '語学', '勉強', '美術館', '博物館', '神社仏閣', 'スポーツ観戦',
  'ペット', '犬', '猫', '植物', 'ガーデニング', 'ボードゲーム', '麻雀', '将棋', 'チェス',
]

export const RANKS = ['A','K','Q','J','T','9','8','7','6','5','4','3','2']
export const SUITS = ['♠','♥','♦','♣']
export const DECK = RANKS.flatMap(rank => SUITS.map(suit => `${rank}${suit}`))

export function pokerExperience(data: PokerProfileExtrasData, at = new Date()): string {
  const y = Number(data.poker_started_year), m = Number(data.poker_started_month)
  if (Number.isInteger(y) && y >= 1900 && Number.isInteger(m) && m >= 1 && m <= 12) {
    const months = Math.max(0, (at.getFullYear() - y) * 12 + at.getMonth() + 1 - m)
    const years = Math.floor(months / 12), rest = months % 12
    return years > 0 ? `${years}年${rest ? `${rest}ヶ月` : ''}` : `${rest}ヶ月`
  }
  return data.poker_years != null ? `${data.poker_years}年` : '未登録'
}

const pill: CSSProperties = { display: 'inline-flex', alignItems: 'center', padding: '7px 11px',
  borderRadius: 999, background: '#111', border: '1px solid #292929', color: '#ddd', fontSize: 12, lineHeight: 1.35 }

export function AdditionalProfileTags({ data }: { data: PokerProfileExtrasData }) {
  const hobbies = Array.isArray(data.hobbies) ? data.hobbies.filter(Boolean).slice(0, 5) : []
  return <>
    {data.main_play && MAIN_PLAY_LABELS[data.main_play] && <span style={pill}>♠ {MAIN_PLAY_LABELS[data.main_play]}</span>}
    {data.poker_frequency && POKER_FREQUENCIES[data.poker_frequency] && <span style={pill}>📅 {POKER_FREQUENCIES[data.poker_frequency]}</span>}
    {hobbies.length > 0 && <div style={{ ...pill, borderRadius: 12, maxWidth: '100%', flexWrap: 'wrap', gap: 5 }}>
      <span style={{ color: '#aaa', whiteSpace: 'nowrap' }}>🎨 ポーカー以外の趣味</span>
      <strong style={{ color: '#fff', fontWeight: 600, overflowWrap: 'anywhere' }}>{hobbies.join(' · ')}</strong>
    </div>}
  </>
}

export function PokerMeaningSection({ data, own = false, onEdit }: { data: PokerProfileExtrasData; own?: boolean; onEdit?: () => void }) {
  if (!data.poker_meaning?.trim() && !own) return null
  return <section style={{ padding: '23px 0', borderBottom: '1px solid #242424' }}>
    <div style={{ fontSize: 17, fontWeight: 800 }}>あなたにとってポーカーとは？</div>
    <div style={{ marginTop: 6, fontSize: 11, color: '#777' }}>WHAT IS POKER TO YOU?</div>
    {data.poker_meaning?.trim() ? <div style={{ marginTop: 14, padding: '20px 17px', border: '1px solid #3c3c3c', background: 'linear-gradient(145deg,#1b1b1b,#0c0c0c)', borderRadius: 16 }}>
      <div style={{ color: '#fff', fontSize: 21, lineHeight: 1.55, fontWeight: 800, overflowWrap: 'anywhere' }}>「{data.poker_meaning}」</div>
      {data.poker_meaning_detail?.trim() && <div style={{ marginTop: 14, color: '#bbb', fontSize: 13, whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', lineHeight: 1.8 }}>{data.poker_meaning_detail}</div>}
    </div> : <button type="button" onClick={onEdit} style={{ marginTop: 12, padding: 15, color: '#ddd', background: '#181818', border: '1px solid #444', borderRadius: 12, width: '100%', textAlign: 'left' }}>あなたのポーカー観を登録する →</button>}
  </section>
}

export function MyHandSection({ data, own = false, onEdit }: { data: PokerProfileExtrasData; own?: boolean; onEdit?: () => void }) {
  const cards = Array.isArray(data.my_hand_cards) ? data.my_hand_cards.filter(v => DECK.includes(v)) : []
  if (cards.length !== 2 && !own) return null
  return <section style={{ padding: '23px 0', borderBottom: '1px solid #242424' }}>
    <div style={{ fontSize: 17, fontWeight: 800 }}>マイハンド</div>
    <div style={{ marginTop: 6, fontSize: 11, color: '#777' }}>MY HAND</div>
    {cards.length === 2 ? <div style={{ marginTop: 15, padding: 16, background: '#111', border: '1px solid #303030', borderRadius: 16 }}>
      <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
        {cards.map(card => {
          const suit = card.slice(-1)
          const rank = card.slice(0, -1)
          const suitColor: Record<string, string> = {
            '♠': '#222936', '♥': '#dc354c', '♦': '#2675d9', '♣': '#15955c',
          }
          const color = suitColor[suit] || '#222936'
          return <div key={card} aria-label={`${rank}${suit}`} style={{
            width: 82, height: 116, background: 'linear-gradient(155deg, #ffffff, #f6f7fa)',
            border: '1px solid #d8dce4', borderRadius: 12, color,
            display: 'flex', flexDirection: 'column', position: 'relative',
            padding: '8px 11px', boxSizing: 'border-box', boxShadow: '0 4px 12px #0007',
          }}>
            <span style={{ fontWeight: 900, fontSize: 27, lineHeight: 1.05, letterSpacing: '-0.6px' }}>{rank}</span>
            <span aria-hidden="true" style={{
              position: 'absolute', top: '43%', left: '50%', transform: 'translate(-50%, -50%)',
              fontSize: 56, fontWeight: 700, lineHeight: 1, fontFamily: 'Georgia, serif',
            }}>{suit}</span>
          </div>
        })}
      </div>
      {data.my_hand_reason?.trim() && <div style={{ marginTop: 15, fontSize: 13, color: '#ccc', whiteSpace: 'pre-wrap', lineHeight: 1.8, textAlign: 'center', overflowWrap: 'anywhere' }}>{data.my_hand_reason}</div>}
    </div> : <button type="button" onClick={onEdit} style={{ marginTop: 12, padding: 15, color: '#ddd', background: '#181818', border: '1px solid #444', borderRadius: 12, width: '100%', textAlign: 'left' }}>お気に入りのハンドを登録する →</button>}
  </section>
}
