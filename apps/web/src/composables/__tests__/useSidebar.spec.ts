import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick } from 'vue'

type ChangeListener = (event: { matches: boolean }) => void

function mockViewport(matches: boolean) {
  const listeners: Array<ChangeListener> = []
  vi.stubGlobal(
    'matchMedia',
    vi.fn(() => ({
      matches,
      addEventListener: (_type: string, listener: ChangeListener) => listeners.push(listener),
    })),
  )
  return (mobile: boolean) => listeners.forEach((listener) => listener({ matches: mobile }))
}

async function loadSidebar() {
  const breakpoint = await import('@/composables/useBreakpoint')
  const sidebar = await import('@/composables/useSidebar')
  breakpoint.initBreakpoint()
  await nextTick()
  return { ...breakpoint.useBreakpoint(), ...sidebar.useSidebar() }
}

describe('useSidebar', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.unstubAllGlobals()
  })

  it('starts expanded on desktop', async () => {
    mockViewport(false)
    const { isMobile, isCollapsed } = await loadSidebar()

    expect(isMobile.value).toBe(false)
    expect(isCollapsed.value).toBe(false)
  })

  it('starts collapsed on mobile', async () => {
    mockViewport(true)
    const { isMobile, isCollapsed } = await loadSidebar()

    expect(isMobile.value).toBe(true)
    expect(isCollapsed.value).toBe(true)
  })

  it('collapses when the viewport becomes mobile and expands back on desktop', async () => {
    const changeViewport = mockViewport(false)
    const { isCollapsed } = await loadSidebar()

    changeViewport(true)
    await nextTick()
    expect(isCollapsed.value).toBe(true)

    changeViewport(false)
    await nextTick()
    expect(isCollapsed.value).toBe(false)
  })
})
