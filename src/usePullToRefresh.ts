import { useEffect, useRef, useState } from 'react'
import type { RefObject } from 'react'

type Options = {
  onRefresh: () => Promise<unknown> | void
  enabled?: boolean
  threshold?: number
}

/** 画面内スクロールが先頭のときだけ、下方向のスワイプでデータを再取得する。 */
export function usePullToRefresh<T extends HTMLElement>(
  containerRef: RefObject<T | null>,
  { onRefresh, enabled = true, threshold = 76 }: Options,
) {
  const [pullDistance, setPullDistance] = useState(0)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [refreshError, setRefreshError] = useState('')
  const refreshRef = useRef(onRefresh)
  const busyRef = useRef(false)
  const startYRef = useRef<number | null>(null)
  const trackingRef = useRef(false)
  const pullRef = useRef(0)
  refreshRef.current = onRefresh

  useEffect(() => {
    const element = containerRef.current
    if (!element || !enabled) {
      startYRef.current = null
      trackingRef.current = false
      pullRef.current = 0
      return
    }

    const reset = () => {
      startYRef.current = null
      trackingRef.current = false
      pullRef.current = 0
      setPullDistance(0)
    }

    // 入力欄・ボタン・編集領域・モーダルから開始したタッチは扱わない。
    const isInteractive = (target: EventTarget | null) => {
      if (!(target instanceof Element)) return true
      return Boolean(target.closest('input,textarea,select,button,a,[contenteditable="true"],[role="dialog"],[role="alertdialog"]'))
    }
    const scrollableAncestorIsScrolled = (target: EventTarget | null) => {
      if (!(target instanceof Element)) return false
      let node: Element | null = target
      while (node && node !== element) {
        if (node.scrollTop > 2 && node.scrollHeight > node.clientHeight + 2) return true
        node = node.parentElement
      }
      return false
    }
    const atTop = () => (window.scrollY <= 2 && !scrollableAncestorIsScrolled(lastTarget))
    let lastTarget: EventTarget | null = null

    const onStart = (event: TouchEvent) => {
      reset()
      if (busyRef.current || event.touches.length !== 1 || window.scrollY > 2 || isInteractive(event.target)) return
      lastTarget = event.target
      if (scrollableAncestorIsScrolled(event.target)) return
      startYRef.current = event.touches[0].clientY
    }
    const onMove = (event: TouchEvent) => {
      if (startYRef.current === null || event.touches.length !== 1) return
      const delta = event.touches[0].clientY - startYRef.current
      if (delta <= 0 || !atTop()) {
        if (trackingRef.current) reset()
        return
      }
      if (event.cancelable) event.preventDefault()
      trackingRef.current = true
      const distance = Math.min(115, delta * 0.45)
      pullRef.current = distance
      setPullDistance(distance)
    }
    const onEnd = () => {
      const shouldRefresh = trackingRef.current && pullRef.current >= threshold && !busyRef.current
      reset()
      if (!shouldRefresh) return
      busyRef.current = true
      setIsRefreshing(true)
      setRefreshError('')
      Promise.resolve()
        .then(() => refreshRef.current())
        .catch((error: unknown) => {
          console.error('Pull to Refresh に失敗:', error)
          setRefreshError('更新に失敗しました。もう一度お試しください。')
        })
        .finally(() => {
          busyRef.current = false
          setIsRefreshing(false)
        })
    }
    element.addEventListener('touchstart', onStart, { passive: true })
    element.addEventListener('touchmove', onMove, { passive: false })
    element.addEventListener('touchend', onEnd, { passive: true })
    element.addEventListener('touchcancel', reset, { passive: true })
    return () => {
      element.removeEventListener('touchstart', onStart)
      element.removeEventListener('touchmove', onMove)
      element.removeEventListener('touchend', onEnd)
      element.removeEventListener('touchcancel', reset)
    }
  }, [containerRef, enabled, threshold])

  return { pullDistance, isRefreshing, refreshError }
}
