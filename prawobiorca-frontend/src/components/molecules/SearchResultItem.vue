<script setup lang="ts">
import RegulationElements from '@/components/molecules/RegulationElements.vue'
import type { SearchResultElement, SearchResultHighlight } from '@/api/generated/model'

const props = defineProps<{
  result: string
  elements: Array<SearchResultElement>
  highlight?: SearchResultHighlight | null
  score: number
  selectedCaseId?: string
  canAddToCase: boolean
}>()

const emit = defineEmits<{
  (
    e: 'add-to-case',
    payload: {
      documentContent: string
      elements: Array<SearchResultElement>
      highlight: SearchResultHighlight | null
    },
  ): void
}>()

function handleAddToCase() {
  emit('add-to-case', {
    documentContent: props.result,
    elements: props.elements,
    highlight: props.highlight ?? null,
  })
}
</script>

<template>
  <el-card shadow="never" class="app-card">
    <RegulationElements :elements="elements" :highlight="highlight" />
    <div class="result-footer">
      <span class="score">Podobieństwo: {{ score.toFixed(3) }}</span>
      <div class="app-card-actions">
        <el-tooltip
          v-if="canAddToCase"
          :disabled="!!selectedCaseId"
          content="Wybierz aktywną sprawę w panelu bocznym, by dodać do niej wyszukany element."
          placement="top"
        >
          <span class="tooltip-wrapper">
            <el-button
              type="primary"
              size="small"
              :disabled="!selectedCaseId"
              @click="handleAddToCase"
            >
              Dodaj do sprawy
            </el-button>
          </span>
        </el-tooltip>
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.result-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--app-space-lg);
  margin-top: var(--app-space-md);
}

.score {
  font-size: 0.8rem;
  color: var(--el-text-color-secondary);
}

.tooltip-wrapper {
  display: inline-block;
  cursor: not-allowed;
}
</style>
