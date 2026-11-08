<script setup lang="ts">
import MenuRoundedIcon from '@iconify-vue/material-symbols/menu-rounded'
import { useSidebar } from '@/composables/useSidebar'

const { toggleCollapsed } = useSidebar()
</script>

<template>
  <header class="app-top-bar">
    <button type="button" class="icon-btn" title="Rozwiń menu" @click="toggleCollapsed">
      <MenuRoundedIcon />
    </button>
    <span class="logo">PRAWOBIORCA</span>
  </header>
</template>

<style scoped>
.app-top-bar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  padding: var(--app-space-xs) var(--app-space-sm);
  background-color: var(--app-navbar-bg);
  box-shadow: var(--app-navbar-shadow);
}

.icon-btn svg {
  font-size: 1.25rem;
}

.logo {
  color: var(--el-color-primary);
  font-size: 1.25rem;
  font-weight: bold;
  letter-spacing: 1px;
}
</style>
