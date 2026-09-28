<script setup lang="ts">
import { regulationTypeOptions } from '@/domain/regulations'
import type { RegulationType } from '@/api/generated/model'

const modelValue = defineModel<RegulationType | undefined>()

function handleChange(value: RegulationType | '' | undefined) {
  modelValue.value = value ? value : undefined
}
</script>

<template>
  <div class="regulation-type-filter-wrapper">
    <label class="filter-label">Typ regulacji:</label>
    <el-select
      :model-value="modelValue ?? ''"
      clearable
      placeholder="Wszystkie typy"
      class="regulation-type-filter"
      @update:model-value="handleChange"
      @clear="handleChange(undefined)"
    >
      <el-option
        v-for="option in regulationTypeOptions"
        :key="option.value"
        :label="option.label"
        :value="option.value"
      />
    </el-select>
  </div>
</template>

<style scoped>
.regulation-type-filter-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 0.9rem;
  color: var(--el-text-color-regular);
  white-space: nowrap;
}

.regulation-type-filter {
  width: 220px;
}
</style>
