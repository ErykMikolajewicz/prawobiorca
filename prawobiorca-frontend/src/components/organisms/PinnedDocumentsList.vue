<script setup lang="ts">
import { computed, ref } from 'vue'
import PinnedDocument from '@/components/molecules/PinnedDocument.vue'
import PinnedDocumentDrawer from '@/components/molecules/PinnedDocumentDrawer.vue'
import type { CaseDocument } from '@/api/generated/model'

const props = defineProps<{ documents: Array<CaseDocument> }>()

const emit = defineEmits<{
  (e: 'unpin', id: string): void
}>()

const selectedDocumentId = ref<string | null>(null)
const selectedDocument = computed(
  () => props.documents.find((document) => document.id === selectedDocumentId.value) ?? null,
)

function handleSelect(id: string) {
  selectedDocumentId.value = id
}

function handleClose() {
  selectedDocumentId.value = null
}

function handleUnpin(id: string) {
  if (selectedDocumentId.value === id) handleClose()
  emit('unpin', id)
}
</script>

<template>
  <div v-if="documents.length > 0" class="pinned-documents">
    <PinnedDocument
      v-for="document in documents"
      :key="document.id"
      :document="document"
      @select="handleSelect"
      @unpin="handleUnpin"
    />
  </div>
  <div v-else>
    <el-empty description="Brak przypiętych artykułów do tej sprawy." />
  </div>

  <PinnedDocumentDrawer :document="selectedDocument" @close="handleClose" @unpin="handleUnpin" />
</template>

<style scoped>
.pinned-documents {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
