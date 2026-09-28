import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus, { ElMessage } from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import './assets/styles.css'
import { useAuthStore } from './stores/auth'
import { setSessionExpiredHandler } from './api/sessionExpiry'
import { useDarkMode } from './composables/useDarkMode'
import { getApiErrorMessage } from './utils/error'

import App from './App.vue'
import router from './router'

useDarkMode()

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(ElementPlus)

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

try {
  await authStore.checkIsLogged()
} catch (error: unknown) {
  ElMessage.error(getApiErrorMessage(error))
}

app.use(router)
app.mount('#app')
