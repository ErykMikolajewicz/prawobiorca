<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { showApiError } from '@/utils/error'
import LoginRoundedIcon from '@iconify-vue/material-symbols/login-rounded'
import LogoutRoundedIcon from '@iconify-vue/material-symbols/logout-rounded'

type Props = {
  collapsed?: boolean
}

defineProps<Props>()

const router = useRouter()
const authStore = useAuthStore()

async function handleLogin() {
  await router.push({ name: 'LoginPage' })
}

async function handleLogout() {
  try {
    await authStore.logout()
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się wylogować.' })
  }
  await router.push({ name: 'MainPage' })
}
</script>

<template>
  <div class="auth-controls">
    <template v-if="collapsed">
      <button
        v-if="authStore.isUserLogged"
        type="button"
        class="icon-btn"
        title="Wyloguj się"
        @click="handleLogout"
      >
        <LogoutRoundedIcon />
      </button>

      <button v-else type="button" class="icon-btn" title="Zaloguj się" @click="handleLogin">
        <LoginRoundedIcon />
      </button>
    </template>

    <template v-else>
      <el-button v-if="authStore.isUserLogged" @click="handleLogout"> Wyloguj się </el-button>

      <el-button v-else type="primary" @click="handleLogin"> Zaloguj się </el-button>
    </template>
  </div>
</template>

<style scoped>
.auth-controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}
</style>
