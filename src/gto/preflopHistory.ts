/** Exact public-action query identity. No strategy or formal presets are inferred. */
export type PreflopAction = { seat: number; action: 'fold' | 'call' | 'check' } |
  { seat: number; action: 'raise'; toBb: string }
const scale = 100000000n
function chips(value: unknown): bigint {
  if (typeof value !== 'string' || value.length > 24 || !/^(0|[1-9]\d*)(\.\d{1,8})?$/.test(value)) throw new Error('履歴のサイズはBB単位の正の数で入力してください。')
  const [whole, fraction = ''] = value.split('.')
  return BigInt(whole) * scale + BigInt(fraction.padEnd(8, '0'))
}
function bb(value: bigint): string {
  const tail = (value % scale).toString().padStart(8, '0').replace(/0+$/, '')
  return `${value / scale}${tail ? `.${tail}` : ''}`
}
export function analyzeHistory(players: number, stackBb: string, value: unknown): {
  history: PreflopAction[]; nextSeat: number | null; raises: number;
} {
  if (!Number.isInteger(players) || players < 2 || players > 9 || !Array.isArray(value) || value.length > 64) throw new Error('人数とアクション履歴を確認してください。')
  const stack = chips(stackBb)
  if (stack <= scale) throw new Error('履歴指定は1BBを超える有効スタックに対応しています。')
  const paid = Array<bigint>(players).fill(0n); paid[0] = scale / 2n; paid[1] = scale
  const active = new Set(Array.from({ length: players }, (_, i) => i))
  let pending = new Set(active), next: number | null = players === 2 ? 0 : 2
  let bet = scale, increment = scale, raises = 0
  const history: PreflopAction[] = []
  for (const raw of Array.from(value)) {
    if (!raw || typeof raw !== 'object' || Array.isArray(raw) || !Number.isInteger(raw.seat) || raw.seat !== next || !pending.has(raw.seat)) throw new Error('履歴の手番がポジションと一致しません。')
    const seat: number = raw.seat
    if (raw.action === 'raise') {
      const target = chips(raw.toBb)
      if (target <= bet || target > stack || (target - bet < increment && target !== stack)) throw new Error('レイズ額は合法な最小額以上、スタック以下で指定してください。')
      increment = target - bet >= increment ? target - bet : increment
      bet = target; paid[seat] = target; raises++
      pending = new Set([...active].filter(p => p !== seat && paid[p] < stack))
      history.push({ seat, action: 'raise', toBb: bb(target) })
    } else {
      if (raw.toBb !== undefined || !['fold', 'call', 'check'].includes(raw.action)) throw new Error('履歴のアクションを確認してください。')
      if (raw.action === 'fold') active.delete(seat)
      else if (raw.action === 'call') {
        if (paid[seat] >= bet) throw new Error('ベットに直面していない場合はチェックを指定してください。')
        paid[seat] = bet < stack ? bet : stack
      } else if (paid[seat] !== bet) throw new Error('ベットに直面しているためチェックできません。')
      pending.delete(seat); history.push({ seat, action: raw.action })
    }
    next = null
    if (active.size > 1 && pending.size) {
      for (let offset = 1; offset <= players; offset++) {
        const candidate = (seat + offset) % players
        if (pending.has(candidate)) { next = candidate; break }
      }
    }
  }
  return { history, nextSeat: next, raises }
}
