import { useEffect, useRef } from "react"

/** 컨테이너 ref를 반환. messages가 바뀔 때마다 맨 아래로 스크롤. */
export function useAutoScroll<T>(deps: T) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight
    }
  }, [deps])

  return ref
}
