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
    shadow="hover"
    class="pinned-document"
    tabindex="0"
    @click="handleSelect"
    @keydown.enter="handleSelect"
  >
    <div class="card-content">
      <div class="document-info">
        <em class="presentation-name">{{ document.presentationName }}</em>
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

.card-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.document-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.header {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.presentation-name {
  font-size: 0.85em;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
