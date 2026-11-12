<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

<template>
  <main v-if="authStore.isCheckingSession || !$route.matched.length" class="app-loading">
    <h1>Prawobiorca</h1>
    <p role="status">Ładowanie aplikacji…</p>
  </main>
  <router-view v-else :key="$route.path" />
</template>

<style scoped>
.app-loading {
  display: flex;
  min-height: 100vh;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>
