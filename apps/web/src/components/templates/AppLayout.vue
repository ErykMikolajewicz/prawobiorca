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

      <div class="content-row">
        <main class="main-content">
          <slot />
        </main>

        <aside v-if="$slots.aside" class="page-aside">
          <slot name="aside" />
        </aside>
      </div>

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

.content-row {
  flex-grow: 1;
  display: flex;
}

.main-content {
  flex-grow: 1;
  min-width: 0;
  padding: var(--app-space-lg);
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  box-sizing: border-box;
  overflow-x: hidden;
}

.page-aside {
  position: sticky;
  top: 0;
  align-self: flex-start;
  flex: 0 0 26rem;
  height: 100vh;
  margin-right: var(--app-space-md);
  overflow-y: auto;
}

@media (width <= 768px) {
  .main-content {
    padding: var(--app-space-sm);
  }
}
</style>
