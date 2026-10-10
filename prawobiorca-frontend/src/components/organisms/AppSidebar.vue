<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import HomeRoundedIcon from '@iconify-vue/material-symbols/home-rounded'
import MenuRoundedIcon from '@iconify-vue/material-symbols/menu-rounded'
import MenuOpenRoundedIcon from '@iconify-vue/material-symbols/menu-open-rounded'
import FolderRoundedIcon from '@iconify-vue/material-symbols/folder-rounded'
import DescriptionRoundedIcon from '@iconify-vue/material-symbols/description-rounded'
import AdminPanelSettingsRoundedIcon from '@iconify-vue/material-symbols/admin-panel-settings-rounded'
import CorporateFareRoundedIcon from '@iconify-vue/material-symbols/corporate-fare-rounded'
import SidebarContextMenu from '@/components/molecules/SidebarContextMenu.vue'
import SidebarCasesList from '@/components/organisms/SidebarCasesList.vue'
import { useSidebar } from '@/composables/useSidebar'
import { useAuthStore } from '@/stores/auth'
import { useCasesStore } from '@/stores/cases'
import { useOrganizationsStore } from '@/stores/organizations'

const route = useRoute()
const { isCollapsed, toggleCollapsed } = useSidebar()
const { isUserLogged, isAdmin } = storeToRefs(useAuthStore())
const casesStore = useCasesStore()
const organizationsStore = useOrganizationsStore()

onMounted(async () => {
  await organizationsStore.load()
  if (isUserLogged.value) {
    await casesStore.load()
  }
})
</script>

<template>
  <el-aside
    :width="isCollapsed ? '64px' : '260px'"
    :class="['app-sidebar', { 'is-collapsed': isCollapsed }]"
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
      <el-sub-menu v-if="isAdmin" index="admin">
        <template #title>
          <el-icon><AdminPanelSettingsRoundedIcon /></el-icon>
          <span>Administracja</span>
        </template>
        <el-menu-item index="/admin/application-templates">
          <el-icon><DescriptionRoundedIcon /></el-icon>
          <template #title>Szablony wniosków</template>
        </el-menu-item>
        <el-menu-item index="/admin/organizations">
          <el-icon><CorporateFareRoundedIcon /></el-icon>
          <template #title>Organizacje</template>
        </el-menu-item>
      </el-sub-menu>
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

    <div class="sidebar-footer">
      <SidebarContextMenu :collapsed="isCollapsed" />
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
  gap: var(--app-space-md);
  padding: var(--app-space-md) var(--app-space-sm);
  box-sizing: border-box;
  overflow: hidden;
  --el-menu-bg-color: transparent;
  --el-menu-item-height: 40px;
  --el-menu-sub-item-height: 40px;
  background-color: transparent;
  border-right: 1px solid var(--app-border-color);
}

.app-sidebar :deep(.icon-btn svg) {
  font-size: 1.25rem;
}

.app-sidebar.is-collapsed {
  align-items: center;
  padding-inline: 0;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-left: var(--app-space-md);
}

.app-sidebar.is-collapsed .sidebar-header {
  padding-left: 0;
}

.logo {
  color: var(--el-color-primary);
  font-size: 1.25rem;
  font-weight: bold;
  letter-spacing: 1px;
}

.sidebar-menu {
  border-right: none;
}

.sidebar-menu .el-icon {
  font-size: 1.25rem;
}

.sidebar-cases {
  flex: 0 1 auto;
}

.sidebar-footer {
  margin-top: auto;
  display: flex;
  justify-content: center;
}
</style>
