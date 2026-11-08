<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import SidebarContent from '@/components/organisms/SidebarContent.vue'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { useSidebar } from '@/composables/useSidebar'
import { useAuthStore } from '@/stores/auth'
import { useCasesStore } from '@/stores/cases'
import { useOrganizationsStore } from '@/stores/organizations'

const { isMobile } = useBreakpoint()
const { isCollapsed } = useSidebar()
const { isUserLogged } = storeToRefs(useAuthStore())
const casesStore = useCasesStore()
const organizationsStore = useOrganizationsStore()

if (isMobile.value) {
  isCollapsed.value = true
}

const isDrawerOpen = computed({
  get: () => !isCollapsed.value,
  set: (isOpen) => {
    isCollapsed.value = !isOpen
  },
})

onMounted(async () => {
  await organizationsStore.load()
  if (isUserLogged.value) {
    await casesStore.load()
  }
})
</script>

<template>
  <el-drawer
    v-if="isMobile"
    v-model="isDrawerOpen"
    direction="ltr"
    size="260px"
    :with-header="false"
    body-class="app-sidebar-drawer-body"
  >
    <SidebarContent />
  </el-drawer>

  <el-aside v-else :width="isCollapsed ? '64px' : '260px'" class="app-sidebar">
    <SidebarContent />
  </el-aside>
</template>

<style scoped>
.app-sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  box-sizing: border-box;
  overflow: hidden;
  background-color: transparent;
  border-right: 1px solid var(--app-border-color);
}
</style>
