<script setup lang="ts">
import { computed } from 'vue'
import { regulationTypeOptions } from '@/domain/regulations'
import type { RegulationType } from '@/api/generated/model'

type Props = {
  regulationType?: RegulationType | null
}

const props = defineProps<Props>()

const hasLabel = computed(() =>
  regulationTypeOptions.some((option) => option.value === props.regulationType),
)
</script>

<template>
  <el-tag v-if="hasLabel" size="small" type="info" effect="plain" class="app-badge">
    <span class="labels">
      <span
        v-for="option in regulationTypeOptions"
        :key="option.value"
        :class="['label', { 'is-hidden': option.value !== regulationType }]"
      >
        {{ option.label }}
      </span>
    </span>
  </el-tag>
</template>

<style scoped>
.labels {
  display: grid;
  justify-items: center;
}

.label {
  grid-area: 1 / 1;
}

.label.is-hidden {
  visibility: hidden;
}
</style>
