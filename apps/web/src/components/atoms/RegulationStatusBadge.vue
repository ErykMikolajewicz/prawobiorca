<script setup lang="ts">
import { computed } from 'vue'
import { preparationStatusOptions } from '@/domain/regulations'
import type { RegulationPreparationStatus } from '@/api/generated/model'

type Props = {
  preparationStatus: RegulationPreparationStatus
}

const props = defineProps<Props>()

const status = computed(() => {
  if (props.preparationStatus === 'PREPARED') {
    return undefined
  }
  return preparationStatusOptions[props.preparationStatus]
})
</script>

<template>
  <el-tag v-if="status" size="small" effect="plain" :type="status.tagType" class="app-badge">
    {{ status.label }}
  </el-tag>
</template>
