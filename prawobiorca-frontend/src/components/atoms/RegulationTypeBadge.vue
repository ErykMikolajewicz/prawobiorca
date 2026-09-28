<script setup lang="ts">
import { computed } from 'vue'
import { regulationTypeOptions } from '@/domain/regulations'
import type { RegulationType } from '@/api/generated/model'

type Props = {
  regulationType?: RegulationType | null
}

const props = defineProps<Props>()

const label = computed(() => {
  if (!props.regulationType) {
    return undefined
  }
  return regulationTypeOptions.find((option) => option.value === props.regulationType)?.label
})
</script>

<template>
  <el-tag v-if="label" size="small" type="info" effect="plain" class="regulation-type-badge">
    {{ label }}
  </el-tag>
</template>

<style scoped>
.regulation-type-badge {
  font-weight: 500;
}
</style>
