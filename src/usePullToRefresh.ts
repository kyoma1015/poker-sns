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
    let locked = false

    const reset = () => {
      startY = null
      gestureTopY = null
      startTarget = null
      dragging = false
      rejected = false
      locked = false
      pullRef.current = 0
      setPullDistance(0)
    }

    const isInteractive = (target: EventTarget | null) =>
      !(target instanceof Element) || Boolean(
        target.closest('input,textarea,select,[contenteditable="true"],[role="dialog"],[role="alertdialog"]'),
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
      if (busyRef.current || event.touches.length !== 1 || isInteractive(event.target) ||
          !(event.target instanceof Node) || !container.contains(event.target)) return
      // タッチ開始がホーム画面内のときだけ追跡する。
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

      if (!locked && (deltaY < -12 || (Math.abs(deltaX) > 16 && Math.abs(deltaX) > Math.abs(deltaY)))) {
        rejected = true
        return
      }

      // 最上部で下方向に動き始めたら即座にタッチを確保する。
      // ブラウザのバウンスが scrollY を変えても途中解除しない。
      if (!locked) {
        if (!atTop()) {
          gestureTopY = null
          return
        }
        if (gestureTopY === null) gestureTopY = fingerY
        if (fingerY - gestureTopY <= 2 || !event.cancelable) return
        locked = true
      }
      dragging = true
      if (event.cancelable) event.preventDefault()
      const distanceMoved = fingerY - (gestureTopY ?? fingerY)
      const travel = Math.max(0, distanceMoved)
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

    container.addEventListener('touchstart', onStart, { passive: true })
    container.addEventListener('touchmove', onMove, { passive: false })
    container.addEventListener('touchend', onEnd, { passive: true })
    container.addEventListener('touchcancel', reset, { passive: true })
    return () => {
      container.removeEventListener('touchstart', onStart)
      container.removeEventListener('touchmove', onMove)
      container.removeEventListener('touchend', onEnd)
      container.removeEventListener('touchcancel', reset)
    }
  }, [containerRef, enabled, threshold])

  return { pullDistance, isRefreshing, refreshError }
}
