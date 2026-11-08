import { ref, watchEffect } from 'vue'

const STORAGE_KEY = 'color-theme'

const isDark = ref(false)
let hasUserChoice = false

export function initDarkMode() {
  const stored = localStorage.getItem(STORAGE_KEY)
  const systemPreference = window.matchMedia('(prefers-color-scheme: dark)')

  hasUserChoice = stored === 'dark' || stored === 'light'
  isDark.value = hasUserChoice ? stored === 'dark' : systemPreference.matches

  systemPreference.addEventListener('change', (event) => {
    if (!hasUserChoice) {
      isDark.value = event.matches
    }
  })

  watchEffect(() => {
    document.documentElement.classList.toggle('dark', isDark.value)
  })
}

function toggleDark() {
  isDark.value = !isDark.value
  hasUserChoice = true
  localStorage.setItem(STORAGE_KEY, isDark.value ? 'dark' : 'light')
}

export function useDarkMode() {
  return { isDark, toggleDark }
}
