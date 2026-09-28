import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick } from 'vue'

type ChangeListener = (event: { matches: boolean }) => void

function mockSystemPreference(matches: boolean) {
  const listeners: Array<ChangeListener> = []
  vi.stubGlobal(
    'matchMedia',
    vi.fn(() => ({
      matches,
      addEventListener: (_type: string, listener: ChangeListener) => listeners.push(listener),
    })),
  )
  return (dark: boolean) => listeners.forEach((listener) => listener({ matches: dark }))
}

async function loadDarkMode() {
  const module = await import('@/composables/useDarkMode')
  module.initDarkMode()
  return module.useDarkMode()
}

describe('useDarkMode', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.unstubAllGlobals()
    localStorage.clear()
    document.documentElement.classList.remove('dark')
  })

  it('follows the system theme while the user has not chosen one', async () => {
    const changeSystemTheme = mockSystemPreference(false)
    const { isDark } = await loadDarkMode()

    expect(isDark.value).toBe(false)

    changeSystemTheme(true)
    await nextTick()

    expect(isDark.value).toBe(true)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(localStorage.getItem('color-theme')).toBeNull()
  })

  it('stores the user choice and ignores later system changes', async () => {
    const changeSystemTheme = mockSystemPreference(false)
    const { isDark, toggleDark } = await loadDarkMode()

    toggleDark()
    changeSystemTheme(false)

    expect(isDark.value).toBe(true)
    expect(localStorage.getItem('color-theme')).toBe('dark')
  })

  it('uses the stored choice over the system theme', async () => {
    localStorage.setItem('color-theme', 'light')
    mockSystemPreference(true)
    const { isDark } = await loadDarkMode()

    expect(isDark.value).toBe(false)
  })
})
