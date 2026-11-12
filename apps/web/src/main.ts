import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { ElMessage, messageConfig } from 'element-plus'
import 'element-plus/es/components/message/style/css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import '@fontsource-variable/inter'
import './assets/styles/index.css'
import { useAuthStore } from './stores/auth'
import { setSessionExpiredHandler } from './api/sessionExpiry'
import { initDarkMode } from './composables/useDarkMode'
import { initBreakpoint } from './composables/useBreakpoint'
import { getApiErrorMessage } from './utils/error'

import App from './App.vue'
import router from './router'

messageConfig.placement = 'top-right'

initDarkMode()
initBreakpoint()

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

const authStore = useAuthStore(pinia)

setSessionExpiredHandler(() => {
  const wasLogged = authStore.isUserLogged
  authStore.resetSession()
  if (wasLogged) {
    ElMessage.error('Sesja wygasła. Zaloguj się ponownie.')
    void router.push({
      name: 'LoginPage',
      query: { redirect: router.currentRoute.value.fullPath },
    })
  }
})

void authStore.checkIsLogged().catch((error: unknown) => {
  ElMessage.error(getApiErrorMessage(error))
})

app.use(router)
app.mount('#app')
