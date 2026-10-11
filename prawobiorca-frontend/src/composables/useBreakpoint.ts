import { ref } from 'vue'

const MOBILE_QUERY = '(max-width: 768px)'

const isMobile = ref(false)

export function initBreakpoint() {
  const mobileQuery = window.matchMedia(MOBILE_QUERY)
  isMobile.value = mobileQuery.matches

  mobileQuery.addEventListener('change', (event) => {
    isMobile.value = event.matches
  })
}

export function useBreakpoint() {
  return { isMobile }
}
