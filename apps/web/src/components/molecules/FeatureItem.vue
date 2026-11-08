<script setup lang="ts">
import type { Component } from 'vue'

type Props = {
  icon: Component
  title: string
  description: string
}
defineProps<Props>()
</script>

<template>
  <div class="feature-item">
    <span class="feature-item-icon">
      <component :is="icon" />
    </span>
    <div>
      <p class="feature-item-title">{{ title }}</p>
      <p class="feature-item-description app-text-secondary">{{ description }}</p>
    </div>
  </div>
</template>

<style scoped>
.feature-item {
  display: flex;
  align-items: center;
  gap: var(--app-space-md);
}

.feature-item-icon {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 50%;
  font-size: 1.5rem;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-8);
}

.feature-item-title {
  margin: 0;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.feature-item-description {
  margin: var(--app-space-xs) 0 0;
}
</style>
