<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import CloseRoundedIcon from '@iconify-vue/material-symbols/close-rounded'

const STORAGE_KEY = 'login-cta-dismissed-on'

const router = useRouter()

const today = new Date().toDateString()
const isVisible = ref(localStorage.getItem(STORAGE_KEY) !== today)

function dismiss() {
  localStorage.setItem(STORAGE_KEY, today)
  isVisible.value = false
}
</script>

<template>
  <section v-if="isVisible" class="login-cta-banner">
    <p class="login-cta-text">
      Zaloguj się, aby skorzystać z
      <router-link :to="{ name: 'FeaturesPage' }" class="login-cta-link">
        dodatkowych funkcji
      </router-link>
    </p>

    <div class="login-cta-actions">
      <el-button type="primary" @click="router.push({ name: 'LoginPage' })">Zaloguj się</el-button>
      <el-button @click="router.push({ name: 'RegisterPage' })">Załóż konto</el-button>
      <button type="button" class="icon-btn" title="Zamknij" @click="dismiss">
        <CloseRoundedIcon />
      </button>
    </div>
  </section>
</template>

<style scoped>
.login-cta-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-md);
  padding: var(--app-space-md) var(--app-space-lg);
  margin-bottom: var(--app-space-lg);
  border-radius: var(--app-radius-lg);
  background: var(--el-color-primary-light-8);
}

.login-cta-text {
  margin: 0;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.login-cta-link {
  color: var(--el-color-primary);
}

.login-cta-actions {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
}

.login-cta-actions .el-button + .el-button {
  margin-left: 0;
}
</style>
