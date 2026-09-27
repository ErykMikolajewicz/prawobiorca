<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/error'

const router = useRouter()
const authStore = useAuthStore()

async function handleLogin() {
  await router.push('/auth/login')
}

async function handleLogout() {
  try {
    await authStore.logout()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, { defaultServerMessage: 'Nie udało się wylogować.' }))
    console.error(error)
  }
  await router.push('/')
}
</script>

<template>
  <div class="auth-controls">
    <el-button v-if="authStore.isUserLogged" @click="handleLogout"> Wyloguj się </el-button>

    <el-button v-else type="primary" @click="handleLogin"> Zaloguj się </el-button>
  </div>
</template>

<style scoped>
.auth-controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}
</style>
