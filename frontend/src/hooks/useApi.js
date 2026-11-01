// frontend/src/hooks/useApi.js
// Custom hook for polling API endpoints with loading/error state.

import { useState, useEffect, useCallback, useRef } from 'react'

/**
 * usePoll — polls an async function at a given interval.
 *
 * @param {Function} fetcher   — async function returning data
 * @param {number}   interval  — polling interval in ms (default 5000)
 * @returns { data, loading, error, refetch }
 */
export function usePoll(fetcher, interval = 5000) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const timerRef              = useRef(null)
  const mountedRef            = useRef(true)

  const fetch_ = useCallback(async () => {
    try {
      const result = await fetcher()
      if (mountedRef.current) {
        setData(result)
        setError(null)
        setLoading(false)
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err.message)
        setLoading(false)
      }
    }
  }, [fetcher])

  useEffect(() => {
    mountedRef.current = true
    fetch_()
    timerRef.current = setInterval(fetch_, interval)
    return () => {
      mountedRef.current = false
      clearInterval(timerRef.current)
    }
  }, [fetch_, interval])

  return { data, loading, error, refetch: fetch_ }
}
