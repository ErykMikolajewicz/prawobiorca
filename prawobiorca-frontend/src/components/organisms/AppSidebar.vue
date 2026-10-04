<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import HomeRoundedIcon from '@iconify-vue/material-symbols/home-rounded'
import MenuRoundedIcon from '@iconify-vue/material-symbols/menu-rounded'
import MenuOpenRoundedIcon from '@iconify-vue/material-symbols/menu-open-rounded'
import FolderRoundedIcon from '@iconify-vue/material-symbols/folder-rounded'
import AuthControls from '@/components/molecules/AuthControls.vue'
import DarkModeToggle from '@/components/molecules/DarkModeToggle.vue'
import SidebarCasesList from '@/components/organisms/SidebarCasesList.vue'
import { useSidebar } from '@/composables/useSidebar'
import { useAuthStore } from '@/stores/auth'
import { useCasesStore } from '@/stores/cases'

const route = useRoute()
const { isCollapsed, toggleCollapsed } = useSidebar()
const { isUserLogged } = storeToRefs(useAuthStore())
const casesStore = useCasesStore()

onMounted(async () => {
  if (isUserLogged.value) {
    await casesStore.load()
  }
})
</script>

<template>
  <el-aside
    :width="isCollapsed ? '64px' : '260px'"
    :class="['app-sidebar', { collapsed: isCollapsed }]"
  >
    <div class="sidebar-header">
      <div v-if="!isCollapsed" class="logo">PRAWOBIORCA</div>
      <button
        type="button"
        class="icon-btn"
        :title="isCollapsed ? 'Rozwiń menu' : 'Zwiń menu'"
        @click="toggleCollapsed"
      >
        <MenuRoundedIcon v-if="isCollapsed" />
        <MenuOpenRoundedIcon v-else />
      </button>
    </div>

    <el-menu
      :collapse="isCollapsed"
      :collapse-transition="false"
      :default-active="route.path"
      router
      class="sidebar-menu"
    >
      <el-menu-item index="/">
        <el-icon><HomeRoundedIcon /></el-icon>
        <template #title>Strona główna</template>
      </el-menu-item>
    </el-menu>

    <template v-if="isUserLogged">
      <button
        v-if="isCollapsed"
        type="button"
        class="icon-btn"
        title="Moje sprawy"
        @click="toggleCollapsed"
      >
        <FolderRoundedIcon />
      </button>
      <SidebarCasesList v-else class="sidebar-cases" />
    </template>
    <p v-else-if="!isCollapsed" class="sidebar-guest-info">
      Zaloguj się, aby zarządzać swoimi sprawami i generować dla nich wnioski.
    </p>

    <div class="sidebar-footer">
      <DarkModeToggle />
      <AuthControls :collapsed="isCollapsed" />
    </div>
  </el-aside>
</template>

<style scoped>
.app-sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 8px;
  box-sizing: border-box;
  overflow: hidden;
  --el-menu-bg-color: transparent;
  --el-menu-item-height: 40px;
  background-color: transparent;
  border-right: 1px solid var(--app-border-color);
}

.app-sidebar :deep(.icon-btn svg) {
  font-size: 20px;
}

.app-sidebar.collapsed {
  align-items: center;
  padding-inline: 0;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-left: 12px;
}

.app-sidebar.collapsed .sidebar-header {
  padding-left: 0;
}

.logo {
  color: var(--el-color-primary);
  font-size: 20px;
  font-weight: bold;
  letter-spacing: 1px;
}

.sidebar-menu {
  border-right: none;

  .el-icon {
    font-size: 20px;
  }
}

.sidebar-cases {
  flex: 0 1 auto;
}

.sidebar-guest-info {
  margin: auto 0 0;
  padding-left: var(--el-menu-base-level-padding);
  font-size: 0.85rem;
  line-height: 1.5;
  color: var(--el-text-color-secondary);

  & + .sidebar-footer {
    margin-top: 0;
  }
}

.sidebar-footer {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.app-sidebar.collapsed .sidebar-footer {
  flex-direction: column;
}
</style>
