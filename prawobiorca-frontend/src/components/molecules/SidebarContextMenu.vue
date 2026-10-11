<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import SchoolRoundedIcon from '@iconify-vue/material-symbols/school-rounded'
import UnfoldMoreRoundedIcon from '@iconify-vue/material-symbols/unfold-more-rounded'
import AuthControls from '@/components/molecules/AuthControls.vue'
import DarkModeToggle from '@/components/molecules/DarkModeToggle.vue'
import { useOrganizationsStore } from '@/stores/organizations'

type Props = {
  collapsed?: boolean
}

defineProps<Props>()

const organizationsStore = useOrganizationsStore()
const { organizations, selectedOrganization, selectedSuborganization } =
  storeToRefs(organizationsStore)

const label = computed(() => selectedOrganization.value?.shortName ?? 'Wybierz organizację')

const title = computed(() =>
  selectedSuborganization.value
    ? `${label.value} · ${selectedSuborganization.value.name}`
    : label.value,
)

const suborganizations = computed(() => selectedOrganization.value?.suborganizations ?? [])

const organizationId = computed<string>({
  get: () => selectedOrganization.value?.id ?? '',
  set: (value) => organizationsStore.select(value ?? '', ''),
})

const suborganizationId = computed<string>({
  get: () => selectedSuborganization.value?.id ?? '',
  set: (value) => organizationsStore.select(organizationId.value, value ?? ''),
})
</script>

<template>
  <el-popover trigger="click" placement="top-start" :width="260">
    <template #reference>
      <button v-if="collapsed" type="button" class="icon-btn" :title="title">
        <SchoolRoundedIcon />
      </button>
      <button v-else type="button" class="context-trigger" :title="title">
        <SchoolRoundedIcon class="context-icon" />
        <span class="context-text">
          <span class="context-label app-text-truncate">{{ label }}</span>
          <span v-if="selectedSuborganization" class="app-text-secondary app-text-truncate">
            {{ selectedSuborganization.name }}
          </span>
        </span>
        <UnfoldMoreRoundedIcon class="context-icon" />
      </button>
    </template>

    <div class="context-menu">
      <span class="app-text-secondary">Organizacja</span>
      <el-select
        v-model="organizationId"
        :teleported="false"
        placeholder="Wszystkie organizacje"
        clearable
      >
        <el-option
          v-for="organization in organizations"
          :key="organization.id"
          :value="organization.id"
          :label="organization.name"
        />
      </el-select>
      <span class="app-text-secondary">Podorganizacja</span>
      <el-select
        v-model="suborganizationId"
        :teleported="false"
        :disabled="!suborganizations.length"
        placeholder="Wszystkie podorganizacje"
        clearable
      >
        <el-option
          v-for="suborganization in suborganizations"
          :key="suborganization.id"
          :value="suborganization.id"
          :label="suborganization.name"
        />
      </el-select>
      <div class="context-menu-actions">
        <DarkModeToggle />
        <AuthControls />
      </div>
    </div>
  </el-popover>
</template>

<style scoped>
.context-trigger {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  width: 100%;
  padding: var(--app-space-sm) var(--app-space-md);
  border: 1px solid var(--app-border-color);
  border-radius: var(--el-border-radius-base);
  background: none;
  color: var(--el-text-color-primary);
  cursor: pointer;
  font: inherit;
  text-align: left;
}

.context-trigger:hover {
  background-color: var(--el-fill-color-light);
}

.context-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
}

.context-text {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}

.context-menu {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
}

.context-menu-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: var(--app-space-sm);
  border-top: 1px solid var(--app-border-color);
}
</style>
