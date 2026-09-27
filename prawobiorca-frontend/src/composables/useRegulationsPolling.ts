import { onUnmounted, watch } from 'vue'

const DEFAULT_INTERVAL_MS = 5000
const DEFAULT_TIMEOUT_MS = 5 * 60 * 1000

type PollingOptions = {
  intervalMs?: number
  timeoutMs?: number
}

/**
 * Odpytuje backend tak długo, jak długo jakakolwiek regulacja czeka na przetworzenie w tle.
 */
export function useRegulationsPolling(
  hasPending: () => boolean,
  refresh: () => Promise<void>,
  options?: PollingOptions,
) {
  const intervalMs = options?.intervalMs ?? DEFAULT_INTERVAL_MS
  const timeoutMs = options?.timeoutMs ?? DEFAULT_TIMEOUT_MS

  let intervalId: ReturnType<typeof setInterval> | null = null
  let startedAt = 0
  let isRefreshing = false

  function stop() {
    if (intervalId !== null) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  async function tick() {
    if (Date.now() - startedAt >= timeoutMs) {
      stop()
      return
    }
    if (isRefreshing || document.visibilityState === 'hidden') {
      return
    }

    isRefreshing = true
    try {
      await refresh()
    } finally {
      isRefreshing = false
    }
  }

  function start() {
    if (intervalId !== null) {
      return
    }
    startedAt = Date.now()
    intervalId = setInterval(tick, intervalMs)
  }

  watch(hasPending, (pending) => (pending ? start() : stop()), { immediate: true })

  onUnmounted(stop)
}
