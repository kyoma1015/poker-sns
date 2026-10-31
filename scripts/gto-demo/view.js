'use strict';
(() => {
  const $ = id => document.getElementById(id)
  const stages = [['rfi', 'RFI'], ['vs_open', '対オープン'], ['vs_3bet', '対3ベット'], ['vs_4bet', '対4ベット']]
  const colors = ['#486581', '#3c956c', '#c15760']
  const names = { fold: 'フォールド', call: 'コール', check: 'チェック', raise_to_5: '2.5BBへレイズ', raise_to_18: '9BBへレイズ', raise_to_42: '21BBへレイズ', raise_to_100: '50BBオールイン' }
  let stage = 'rfi', mode = 'flop_controller', hand = 'AA'
  const buttons = new Map(), stageButtons = new Map()
  function element(tag, text, parent, className) {
    const e = document.createElement(tag);if (text !== null) e.textContent = text
    if (className) e.className = className
    if (parent) parent.append(e)
    return e
  }
  function render() {
    const model = DATA.models[mode], context = model.contexts[stage], precision = DATA.precision.models[mode].contexts[stage]
    if (model.policy_digest !== DATA.precision.fixed_policy_digests[mode] || context.actor !== precision.actor || JSON.stringify(context.actions) !== JSON.stringify(precision.actions)) throw Error('計算データの条件が一致しません。')
    const row = context.hands[hand], ev = precision.hands[hand]
    for (const [key, b] of stageButtons) b.setAttribute('aria-pressed', String(key === stage))
    $('position').textContent = `${context.actor === 0 ? 'SB／BTN' : 'BB'}の判断 · ${stages.find(x => x[0] === stage)[1]} · 169 / 169ハンド`
    $('legend').replaceChildren()
    context.actions.forEach((action, i) => {const label = element('span', null, $('legend'));const swatch = element('i', null, label);swatch.style.backgroundColor = colors[i];element('span', names[action] ?? action, label)})
    for (const [h, b] of buttons) {
      const f = context.hands[h].frequencies;let total = 0
      b.style.background = `linear-gradient(90deg,${f.map((x, i) => {const start = total;total += x * 100;return `${colors[i]} ${start}%,${colors[i]} ${total}%`}).join(',')})`
      b.setAttribute('aria-pressed', String(h === hand));b.tabIndex = h === hand ? 0 : -1
    }
    $('hand').textContent = hand;$('ev').textContent = `モデルEV ${ev.ev_bb.toFixed(3)} BB`
    $('interval').textContent = `同時99%区間 [${ev.interval_bb.map(x => x.toFixed(3)).join(', ')}] BB · 半径 ${ev.radius_bb.toFixed(3)} BB`
    $('actions').replaceChildren()
    context.actions.forEach((action, i) => {const line = element('div', null, $('actions'), 'action');element('strong', `${names[action] ?? action} ${(row.frequencies[i] * 100).toFixed(1)}%`, line);element('small', `EV ${ev.action_ev_bb[i].toFixed(3)} BB ／区間 [${ev.action_intervals_bb[i].map(x => x.toFixed(3)).join(', ')}]`, line)})
    $('exact').textContent = ev.radius_bb === 0 ? 'この固定モデル内では標本誤差なし。実ゲーム精度の保証ではありません。' : 'モデル内の標本誤差です。実ゲームへの近似誤差はUNKNOWNです。'
    $('bounds').textContent = `期待継続モデルの全体NashConv区間 [${DATA.precision.expected_controller_game_bounds[mode].nashconv_interval_bb.map(x => x.toFixed(4)).join(', ')}] BB。実ゲームの収束合格は未判定です。`
    $('coverage').textContent = `各クラス対256標本。all-in確定セル ${DATA.precision.exact_cells.exact_showdown_cells} / 28,561。未確定セルを全列挙済みとは扱いません。`
    $('policy').textContent = `固定方策 SHA256：${model.policy_digest}`
  }
  function choose(h, focus = false) {hand = h;render();if (focus) buttons.get(h).focus()}
  try {
    stages.forEach(([key, text]) => {const b = element('button', text, $('stages'));b.type = 'button';b.dataset.stage = key;b.addEventListener('click', () => {stage = key;render()});stageButtons.set(key, b)})
    DATA.grid.flat().forEach((h, i) => {const b = element('button', h, $('grid'));b.type = 'button';b.dataset.hand = h;b.setAttribute('aria-label', h);b.addEventListener('click', () => choose(h));b.addEventListener('keydown', e => {const delta = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: 13, ArrowUp: -13 }[e.key];if (delta !== undefined) {e.preventDefault();choose(DATA.grid.flat()[(i + delta + 169) % 169], true)}});buttons.set(h, b)})
    $('mode').addEventListener('change', e => {mode = e.target.value;render()})
    render();$('app').hidden = false
  } catch (e) {$('app').hidden = true;$('error').textContent = `表示できません：${e.message}`;$('error').hidden = false}
})()
