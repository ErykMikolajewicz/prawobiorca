<script setup lang="ts">
import AppSidebar from '@/components/organisms/AppSidebar.vue'
import AppFooter from '@/components/organisms/AppFooter.vue'
import AppTopBar from '@/components/organisms/AppTopBar.vue'
import { useBreakpoint } from '@/composables/useBreakpoint'

const { isMobile } = useBreakpoint()
</script>

<template>
  <div class="page-container">
    <AppSidebar />

    <div class="content-column">
      <AppTopBar v-if="isMobile" />

      <main class="main-content">
        <slot />
      </main>

      <AppFooter />
    </div>
  </div>
</template>

<style scoped>
.page-container {
  display: flex;
  min-height: 100vh;
}

.content-column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex-grow: 1;
  padding: var(--app-space-lg);
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  box-sizing: border-box;
  overflow-x: hidden;
}

@media (width <= 768px) {
  .main-content {
    padding: var(--app-space-sm);
  }
}
</style>
