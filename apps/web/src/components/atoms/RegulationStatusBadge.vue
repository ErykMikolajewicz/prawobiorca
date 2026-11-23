<script setup lang="ts">
import { computed } from 'vue'
import { preparationFailureReasonLabels, preparationStatusOptions } from '@/domain/regulations'
import type {
  RegulationPreparationFailureReason,
  RegulationPreparationStatus,
} from '@/api/generated/model'

type Props = {
  preparationStatus: RegulationPreparationStatus
  failureReason?: RegulationPreparationFailureReason | null
}

const props = defineProps<Props>()

const status = computed(() => {
  if (props.preparationStatus === 'PREPARED') {
    return undefined
  }
  return preparationStatusOptions[props.preparationStatus]
})
const failureReason = computed(() =>
  props.preparationStatus === 'FAILED' && props.failureReason
    ? preparationFailureReasonLabels[props.failureReason]
    : undefined,
)
</script>

<template>
  <el-tooltip v-if="status" :disabled="!failureReason" :content="failureReason" placement="top">
    <el-tag size="small" effect="plain" :type="status.tagType" class="app-badge">
      {{ status.label }}
    </el-tag>
  </el-tooltip>
</template>
