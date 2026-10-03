<script setup lang="ts">
import { computed } from 'vue'
import { generationStatusOptions } from '@/domain/applications'
import type { ApplicationGenerationStatus } from '@/api/generated/model'

type Props = {
  generationStatus: ApplicationGenerationStatus
}

const props = defineProps<Props>()

const status = computed(() => {
  if (props.generationStatus === 'GENERATED') {
    return undefined
  }
  return generationStatusOptions[props.generationStatus]
})
</script>

<template>
  <el-tag
    v-if="status"
    size="small"
    effect="plain"
    :type="status.tagType"
    class="application-status-badge"
  >
    {{ status.label }}
  </el-tag>
</template>

<style scoped>
.application-status-badge {
  font-weight: 500;
}
</style>
