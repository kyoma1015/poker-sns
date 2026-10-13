import { useEffect, useRef, useState } from 'react'
import type { RefObject } from 'react'

type Options = {
  onRefresh: () => Promise<unknown> | void
  enabled?: boolean
  threshold?: number
}

/** ページ最上部での下方向ドラッグ距離だけで更新を決める（速度非依存）。 */
export function usePullToRefresh<T extends HTMLElement>(
  containerRef: RefObject<T | null>,
  { onRefresh, enabled = true, threshold = 76 }: Options,
) {
  const [pullDistance, setPullDistance] = useState(0)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [refreshError, setRefreshError] = useState('')
  const refreshRef = useRef(onRefresh)
  const busyRef = useRef(false)
  const pullRef = useRef(0)
  refreshRef.current = onRefresh

  useEffect(() => {
    const container = containerRef.current
    if (!container || !enabled) return

    let startY: number | null = null
    let startX = 0
    let startTarget: EventTarget | null = null
    let gestureTopY: number | null = null
    let dragging = false
    let rejected = false

    const reset = () => {
      startY = null
      gestureTopY = null
      startTarget = null
      dragging = false
      rejected = false
      pullRef.current = 0
      setPullDistance(0)
    }

    const isInteractive = (target: EventTarget | null) =>
      !(target instanceof Element) || Boolean(
        target.closest('input,textarea,select,button,a,[contenteditable="true"],[role="dialog"],[role="alertdialog"]'),
      )

    const hasScrolledInnerContainer = (target: EventTarget | null) => {
      if (!(target instanceof Element)) return false
      let node: Element | null = target
      while (node && node !== container) {
        if (node.scrollHeight > node.clientHeight + 2 && node.scrollTop > 2) return true
        node = node.parentElement
      }
      return false
    }

    const atTop = () => {
      const root = document.scrollingElement
      const pageTop = Math.max(window.scrollY, root?.scrollTop ?? 0)
      return pageTop <= 4 && !hasScrolledInnerContainer(startTarget)
    }

    const onStart = (event: TouchEvent) => {
      reset()
      if (busyRef.current || event.touches.length !== 1 || isInteractive(event.target)) return
      // イベントはdocumentで追跡。上部ヘッダーからのドラッグも途中で失わない。
      startTarget = event.target
      startY = event.touches[0].clientY
      startX = event.touches[0].clientX
      if (atTop()) gestureTopY = startY
    }

    const onMove = (event: TouchEvent) => {
      if (startY === null || rejected || event.touches.length !== 1) return
      const fingerY = event.touches[0].clientY
      const deltaY = fingerY - startY
      const deltaX = event.touches[0].clientX - startX

      if (!dragging && (deltaY < -12 || (Math.abs(deltaX) > 16 && Math.abs(deltaX) > Math.abs(deltaY)))) {
        rejected = true
        return
      }

      // ページがスクロール途中なら、最上部に来るまでは通常スクロールを妨げない。
      if (!atTop()) {
        if (dragging) reset()
        return
      }
      // 指を置いた時点で最上部でなくても、最上部へ到達した地点を起点にする。
      if (gestureTopY === null) gestureTopY = fingerY
      const distanceMoved = fingerY - gestureTopY
      if (distanceMoved <= 6) return

      dragging = true
      // ブラウザ標準のバウンス/更新が距離計測を奪わないようにする。
      if (event.cancelable) event.preventDefault()
      const travel = distanceMoved - 6
      // 解除前は指にほぼ1:1で追従。閾値到達後だけ軽い抵抗を付ける。
      const distance = Math.min(160, travel <= threshold ? travel : threshold + (travel - threshold) * 0.35)
      pullRef.current = distance
      setPullDistance(distance)
    }

    const onEnd = () => {
      const shouldRefresh = dragging && pullRef.current >= threshold && !busyRef.current
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

    document.addEventListener('touchstart', onStart, { passive: true })
    document.addEventListener('touchmove', onMove, { passive: false })
    document.addEventListener('touchend', onEnd, { passive: true })
    document.addEventListener('touchcancel', reset, { passive: true })
    return () => {
      document.removeEventListener('touchstart', onStart)
      document.removeEventListener('touchmove', onMove)
      document.removeEventListener('touchend', onEnd)
      document.removeEventListener('touchcancel', reset)
    }
  }, [containerRef, enabled, threshold])

  return { pullDistance, isRefreshing, refreshError }
}
