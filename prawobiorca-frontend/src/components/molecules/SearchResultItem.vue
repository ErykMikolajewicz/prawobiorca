<script setup lang="ts">
import RegulationElements from '@/components/atoms/RegulationElements.vue'
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
  <el-card shadow="never" class="app-result-card">
    <RegulationElements :elements="elements" :highlight="highlight" />
    <div class="result-footer">
      <span class="score">Podobieństwo: {{ score.toFixed(3) }}</span>
      <div class="actions">
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
.app-result-card {
  --el-card-bg-color: #faf9fd;
  --el-card-border-color: #ebe8f1;
}

html.dark .app-result-card {
  --el-card-bg-color: #18181a;
  --el-card-border-color: #262628;
}

.result-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 16px;
  margin-top: 0.75rem;
}

.score {
  font-size: 0.8em;
  color: var(--el-text-color-secondary, #909399);
}

.actions {
  flex-shrink: 0;
}

.tooltip-wrapper {
  display: inline-block;
  cursor: not-allowed;
}
</style>
