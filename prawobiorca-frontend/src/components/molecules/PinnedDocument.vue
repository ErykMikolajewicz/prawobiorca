<script setup lang="ts">
import { Close } from '@element-plus/icons-vue'
import type { CaseDocument } from '@/api/generated/model'

type Props = { document: CaseDocument }
const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'select', id: string): void
  (e: 'unpin', id: string): void
}>()

function handleSelect() {
  emit('select', props.document.id)
}

function handleUnpin() {
  emit('unpin', props.document.id)
}
</script>

<template>
  <el-card
    shadow="never"
    class="pinned-document app-card is-interactive"
    tabindex="0"
    @click="handleSelect"
    @keydown.enter="handleSelect"
  >
    <div class="app-card-content">
      <div class="document-info">
        <em class="app-text-secondary app-text-truncate">{{ document.presentationName }}</em>
        <strong v-if="document.header" class="header">{{ document.header }}</strong>
      </div>
      <el-button
        type="danger"
        size="small"
        :icon="Close"
        circle
        plain
        title="Odepnij"
        aria-label="Odepnij"
        @click.stop="handleUnpin"
      />
    </div>
  </el-card>
</template>

<style scoped>
.pinned-document {
  cursor: pointer;
}

.app-card-content {
  align-items: flex-start;
  gap: var(--app-space-sm);
}

.document-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-xs);
}

.header {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
