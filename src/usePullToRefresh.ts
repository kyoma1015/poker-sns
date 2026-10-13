import { useEffect, useRef, useState } from 'react'
import type { RefObject } from 'react'

type Options = {
  onRefresh: () => Promise<unknown> | void
  enabled?: boolean
  threshold?: number
}

/** 最上部から下へ引っ張った距離で更新する。スワイプ速度には依存しない。 */
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
    const element = containerRef.current
    if (!element || !enabled) return

    let startY: number | null = null
    let startX = 0
    let startTarget: EventTarget | null = null
    let dragging = false
    let rejected = false

    const reset = () => {
      startY = null
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
      while (node && node !== element) {
        if (node.scrollTop > 2 && node.scrollHeight > node.clientHeight + 2) return true
        node = node.parentElement
      }
      return false
    }

    const atTop = () => window.scrollY <= 3 && !hasScrolledInnerContainer(startTarget)

    const onStart = (event: TouchEvent) => {
      reset()
      if (busyRef.current || event.touches.length !== 1 || !atTop() || isInteractive(event.target)) return
      startTarget = event.target
      startY = event.touches[0].clientY
      startX = event.touches[0].clientX
    }

    const onMove = (event: TouchEvent) => {
      if (startY === null || rejected || event.touches.length !== 1) return
      const deltaY = event.touches[0].clientY - startY
      const deltaX = event.touches[0].clientX - startX

      // 横スワイプや上方向のスクロールでは更新操作を始めない。
      if (!dragging && (deltaY < -8 || (Math.abs(deltaX) > 12 && Math.abs(deltaX) > Math.abs(deltaY)))) {
        rejected = true
        return
      }
      if (deltaY <= 8 || !atTop()) return

      // 最初の8pxだけ遊びを設ける。以降は移動距離で判定し、速度は見ない。
      dragging = true
      if (event.cancelable) event.preventDefault()
      const travel = deltaY - 8
      // 更新が成立するまでは素直に追従し、成立後は抵抗を加える。
      const distance = Math.min(140, travel <= threshold ? travel : threshold + (travel - threshold) * 0.35)
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
