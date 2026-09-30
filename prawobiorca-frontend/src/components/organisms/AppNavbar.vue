<script setup lang="ts">
import AuthControls from '@/components/molecules/AuthControls.vue'
import DarkModeToggle from '@/components/molecules/DarkModeToggle.vue'
</script>

<template>
  <el-header class="app-navbar">
    <div class="logo">PRAWOBIORCA</div>

    <div class="nav-controls">
      <DarkModeToggle />
      <AuthControls />
    </div>
  </el-header>
</template>

<style scoped>
.app-navbar {
  background-color: var(--app-navbar-bg);
  border-bottom: 2px solid transparent;
  border-image: linear-gradient(90deg, var(--el-color-primary), transparent) 1;
  box-shadow: var(--app-navbar-shadow);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.nav-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo {
  color: var(--el-color-primary);
  font-size: 20px;
  font-weight: bold;
  letter-spacing: 1px;
}
</style>
