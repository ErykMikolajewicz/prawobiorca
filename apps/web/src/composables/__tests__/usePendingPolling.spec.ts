import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { defineComponent, ref, h } from 'vue'
import { mount } from '@vue/test-utils'
import { usePendingPolling } from '@/composables/usePendingPolling'

function mountPolling(
  pendingIds: () => Array<string>,
  refresh: () => Promise<void>,
  options?: { intervalMs?: number; timeoutMs?: number },
) {
  return mount(
    defineComponent({
      setup() {
        usePendingPolling(pendingIds, refresh, options)
        return () => h('div')
      },
    }),
  )
}

describe('usePendingPolling', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('polls while some regulation is pending and stops once none is', async () => {
    const pending = ref(['a'])
    const refresh = vi.fn().mockResolvedValue(undefined)

    mountPolling(() => pending.value, refresh, { intervalMs: 1000 })

    await vi.advanceTimersByTimeAsync(2000)
    expect(refresh).toHaveBeenCalledTimes(2)

    pending.value = []
    await vi.advanceTimersByTimeAsync(5000)
    expect(refresh).toHaveBeenCalledTimes(2)
  })

  it('does not poll when nothing is pending', async () => {
    const refresh = vi.fn().mockResolvedValue(undefined)

    mountPolling(() => [], refresh, { intervalMs: 1000 })

    await vi.advanceTimersByTimeAsync(5000)
    expect(refresh).not.toHaveBeenCalled()
  })

  it('stops polling after the timeout is reached', async () => {
    const refresh = vi.fn().mockResolvedValue(undefined)

    mountPolling(() => ['a'], refresh, { intervalMs: 1000, timeoutMs: 3000 })

    await vi.advanceTimersByTimeAsync(10000)
    expect(refresh).toHaveBeenCalledTimes(2)
  })

  it('resumes polling after the timeout when a new regulation becomes pending', async () => {
    const pending = ref(['a'])
    const refresh = vi.fn().mockResolvedValue(undefined)

    mountPolling(() => pending.value, refresh, { intervalMs: 1000, timeoutMs: 3000 })

    await vi.advanceTimersByTimeAsync(10000)
    expect(refresh).toHaveBeenCalledTimes(2)

    pending.value = ['a', 'b']
    await vi.advanceTimersByTimeAsync(2000)
    expect(refresh).toHaveBeenCalledTimes(4)
  })

  it('keeps the polling pace when another element becomes pending', async () => {
    const pending = ref(['a'])
    const refresh = vi.fn().mockResolvedValue(undefined)

    mountPolling(() => pending.value, refresh, { intervalMs: 1000 })
    await vi.advanceTimersByTimeAsync(1000)

    pending.value = ['a', 'b']
    await vi.advanceTimersByTimeAsync(2000)

    expect(refresh).toHaveBeenCalledTimes(3)
  })

  it('does not start a refresh before the previous one has finished', async () => {
    let finishRefresh: (() => void) | undefined
    const refresh = vi
      .fn()
      .mockImplementationOnce(() => new Promise<void>((resolve) => (finishRefresh = resolve)))
      .mockResolvedValue(undefined)

    mountPolling(() => ['a'], refresh, { intervalMs: 1000 })

    await vi.advanceTimersByTimeAsync(3000)
    expect(refresh).toHaveBeenCalledTimes(1)

    finishRefresh?.()
    await vi.advanceTimersByTimeAsync(1000)
    expect(refresh).toHaveBeenCalledTimes(2)
  })

  it('does not refresh while the browser tab is hidden', async () => {
    const visibilityState = vi.spyOn(document, 'visibilityState', 'get').mockReturnValue('hidden')
    const refresh = vi.fn().mockResolvedValue(undefined)

    mountPolling(() => ['a'], refresh, { intervalMs: 1000 })

    await vi.advanceTimersByTimeAsync(3000)
    expect(refresh).not.toHaveBeenCalled()

    visibilityState.mockReturnValue('visible')
    await vi.advanceTimersByTimeAsync(1000)
    expect(refresh).toHaveBeenCalledTimes(1)

    visibilityState.mockRestore()
  })

  it('polls every 5 seconds by default', async () => {
    const refresh = vi.fn().mockResolvedValue(undefined)

    mountPolling(() => ['a'], refresh)

    await vi.advanceTimersByTimeAsync(4999)
    expect(refresh).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(1)
    expect(refresh).toHaveBeenCalledTimes(1)
  })

  it('stops polling when the component is unmounted', async () => {
    const refresh = vi.fn().mockResolvedValue(undefined)

    const wrapper = mountPolling(() => ['a'], refresh, { intervalMs: 1000 })

    await vi.advanceTimersByTimeAsync(1000)
    expect(refresh).toHaveBeenCalledTimes(1)

    wrapper.unmount()
    await vi.advanceTimersByTimeAsync(5000)
    expect(refresh).toHaveBeenCalledTimes(1)
  })
})
