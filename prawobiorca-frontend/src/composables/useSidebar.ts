import { ref, watch } from 'vue'
import { useBreakpoint } from '@/composables/useBreakpoint'

const { isMobile } = useBreakpoint()

const isCollapsed = ref(isMobile.value)

watch(isMobile, (mobile) => {
  isCollapsed.value = mobile
})

function toggleCollapsed() {
  isCollapsed.value = !isCollapsed.value
}

export function useSidebar() {
  return { isCollapsed, toggleCollapsed }
}
