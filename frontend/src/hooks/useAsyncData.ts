import { useCallback, useEffect, useState } from "react"

export interface AsyncData<T> {
  data: T | null
  loading: boolean
  error: unknown
  reload: () => void
  setData: (value: T) => void
}

/**
 * Runs a loader on mount and whenever `deps` change, tracking the three states
 * every page here needs to distinguish: loading, failed, and loaded (which may
 * legitimately be empty).
 */
export function useAsyncData<T>(loader: () => Promise<T>, deps: unknown[] = []): AsyncData<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<unknown>(null)
  const [reloadToken, setReloadToken] = useState(0)

  const reload = useCallback(() => setReloadToken((token) => token + 1), [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    loader()
      .then((result) => {
        if (!cancelled) setData(result)
      })
      .catch((loadError: unknown) => {
        if (!cancelled) {
          // Null, not stale data: a failed reload must never leave the previous
          // result on screen next to an error message.
          setData(null)
          setError(loadError)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, reloadToken])

  return { data, loading, error, reload, setData }
}
