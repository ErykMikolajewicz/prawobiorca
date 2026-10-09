<script setup lang="ts">
import { computed } from 'vue'
import { templateStatusOptions } from '@/domain/applicationTemplates'
import type { ApplicationTemplateStatus } from '@/api/generated/model'

type Props = {
  status: ApplicationTemplateStatus
}

const props = defineProps<Props>()

const statusOption = computed(() => templateStatusOptions[props.status])
</script>

<template>
  <el-tag size="small" effect="plain" :type="statusOption.tagType" class="template-status-badge">
    {{ statusOption.label }}
  </el-tag>
</template>

<style scoped>
.template-status-badge {
  font-weight: 500;
}
</style>
