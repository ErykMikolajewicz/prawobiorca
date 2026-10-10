<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import RegulationElements from '@/components/atoms/RegulationElements.vue'
import type { CaseDocument } from '@/api/generated/model'

const props = defineProps<{ document: CaseDocument | null }>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'unpin', id: string): void
}>()

const isOpen = computed({
  get: () => props.document !== null,
  set: (value) => {
    if (!value) emit('close')
  },
})

const shownDocument = ref<CaseDocument | null>(props.document)

watch(
  () => props.document,
  (document) => {
    if (document) shownDocument.value = document
  },
)

function handleUnpin() {
  if (props.document) emit('unpin', props.document.id)
}
</script>

<template>
  <el-drawer
    v-model="isOpen"
    direction="rtl"
    :modal="false"
    size="min(40rem, 100vw)"
    header-class="pinned-document-drawer-header"
  >
    <template #header>
      <div v-if="shownDocument" class="drawer-header">
        <em v-if="shownDocument.header" class="presentation-name">
          {{ shownDocument.presentationName }}
        </em>
        <h3 class="title">{{ shownDocument.header ?? shownDocument.presentationName }}</h3>
      </div>
    </template>

    <template v-if="shownDocument">
      <RegulationElements
        v-if="shownDocument.elements.length"
        :elements="shownDocument.elements"
        :highlight="shownDocument.highlight"
      />
      <p v-else class="content">{{ shownDocument.content }}</p>
    </template>

    <template #footer>
      <el-button type="danger" @click="handleUnpin">Odepnij</el-button>
    </template>
  </el-drawer>
</template>

<style scoped>
.drawer-header {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-xs);
}

.title {
  margin: 0;
}

.presentation-name {
  font-size: 0.85rem;
  color: var(--el-text-color-secondary);
}

.content {
  margin: 0;
  white-space: pre-line;
  line-height: 1.6;
}
</style>
