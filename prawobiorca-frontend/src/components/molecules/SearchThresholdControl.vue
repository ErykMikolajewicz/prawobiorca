<script setup lang="ts">
import { ref, watch } from 'vue'

import { defaultThreshold, isPresetThreshold, thresholdPresets } from '@/domain/search'

const props = defineProps<{
  canUseAdvanced: boolean
}>()

const threshold = defineModel<number>({ required: true })

const thresholdMarks = { 0.5: '0.5', 0.6: '0.6', 0.7: '0.7', 0.8: '0.8' }

const isAdvanced = ref(props.canUseAdvanced && !isPresetThreshold(threshold.value))

watch(
  isAdvanced,
  (isAdvancedThreshold) => {
    if (!isAdvancedThreshold && !isPresetThreshold(threshold.value)) {
      threshold.value = defaultThreshold
    }
  },
  { immediate: true },
)
</script>

<template>
  <div class="threshold-control">
    <el-slider
      v-if="isAdvanced"
      v-model="threshold"
      :min="0.3"
      :max="0.9"
      :step="0.01"
      :marks="thresholdMarks"
      :show-tooltip="false"
      class="threshold-slider"
    />
    <span v-if="isAdvanced" class="threshold-value">
      {{ threshold.toFixed(2) }}
    </span>
    <el-select v-else v-model="threshold">
      <el-option
        v-for="preset in thresholdPresets"
        :key="preset.value"
        :label="preset.label"
        :value="preset.value"
      />
    </el-select>
  </div>
  <el-checkbox v-if="canUseAdvanced" v-model="isAdvanced">Zaawansowane</el-checkbox>
</template>

<style scoped>
.threshold-control {
  display: flex;
  align-items: center;
  gap: var(--app-space-lg);
  width: 100%;
}

.threshold-slider {
  flex: 1;
}

.threshold-value {
  color: var(--el-text-color-primary);
  min-width: 40px;
  text-align: center;
  font-weight: 500;
}
</style>
