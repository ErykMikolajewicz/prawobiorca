<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useOrganizationsStore } from '@/stores/organizations'

const organizationsStore = useOrganizationsStore()
const { organizations, selectedOrganization, selectedSuborganization } =
  storeToRefs(organizationsStore)

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
  <div class="regulation-organization-filter-wrapper">
    <label class="filter-label">Organizacja:</label>
    <el-select
      v-model="organizationId"
      clearable
      placeholder="Wszystkie organizacje"
      class="regulation-organization-filter"
    >
      <el-option
        v-for="organization in organizations"
        :key="organization.id"
        :label="organization.name"
        :value="organization.id"
      />
    </el-select>
  </div>
  <div class="regulation-organization-filter-wrapper">
    <label class="filter-label">Podorganizacja:</label>
    <el-select
      v-model="suborganizationId"
      :disabled="!suborganizations.length"
      clearable
      placeholder="Wszystkie podorganizacje"
      class="regulation-organization-filter"
    >
      <el-option
        v-for="suborganization in suborganizations"
        :key="suborganization.id"
        :label="suborganization.name"
        :value="suborganization.id"
      />
    </el-select>
  </div>
</template>

<style scoped>
.regulation-organization-filter-wrapper {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
}

.filter-label {
  font-size: 0.9rem;
  color: var(--el-text-color-regular);
  white-space: nowrap;
}

.regulation-organization-filter {
  width: 220px;
}

@media (width <= 768px) {
  .regulation-organization-filter-wrapper {
    flex-direction: column;
    align-items: stretch;
    gap: var(--app-space-xs);
    width: 100%;
  }

  .regulation-organization-filter {
    width: 100%;
  }
}
</style>
