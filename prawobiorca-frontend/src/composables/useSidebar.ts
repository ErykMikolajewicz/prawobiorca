import { ref } from 'vue'

const MOBILE_MAX_WIDTH = 768

const isCollapsed = ref(window.innerWidth <= MOBILE_MAX_WIDTH)

function toggleCollapsed() {
  isCollapsed.value = !isCollapsed.value
}

export function useSidebar() {
  return { isCollapsed, toggleCollapsed }
}
