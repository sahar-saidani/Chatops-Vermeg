import { useEffect, useState } from "react"

/**
 * Delays propagating a fast-changing value, so filtering does not re-run on
 * every keystroke.
 *
 * <p>Used where the filtered collection is large enough for the work to show:
 * the log agent alone has thousands of stored events, and re-filtering that
 * list per character is visible. It is deliberately NOT used on small
 * already-loaded lists such as Users, where filtering costs nothing and a
 * delay would only make typing feel laggy. No search here triggers a network
 * request, so debouncing is a rendering concern rather than a traffic one.
 */
export function useDebouncedValue<T>(value: T, delayMs = 250): T {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs)
    return () => clearTimeout(timer)
  }, [value, delayMs])

  return debounced
}
