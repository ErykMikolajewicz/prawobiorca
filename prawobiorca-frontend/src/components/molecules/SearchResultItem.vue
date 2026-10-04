<script setup lang="ts">
import { computed } from 'vue'
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
  (e: 'add-to-case', payload: { documentContent: string }): void
}>()

const SUB_ELEMENT_PATTERN = /^(\d+\)|[a-z]\))\s/

type ResultBlock = { subsection: string | null; lines: Array<string>; highlighted: boolean }

function isHighlighted(elementIndex: number) {
  const highlight = props.highlight

  return (
    !!highlight && elementIndex >= highlight.start_element && elementIndex <= highlight.end_element
  )
}

const blocks = computed<Array<ResultBlock>>(() => {
  const result: Array<ResultBlock> = []

  for (const [elementIndex, element] of props.elements.entries()) {
    const lastBlock = result[result.length - 1]
    const highlighted = isHighlighted(elementIndex)

    if (lastBlock && lastBlock.subsection === element.subsection) {
      lastBlock.lines.push(element.text)
      lastBlock.highlighted ||= highlighted
    } else {
      result.push({ subsection: element.subsection, lines: [element.text], highlighted })
    }
  }

  return result
})

function isSubLine(line: string) {
  return SUB_ELEMENT_PATTERN.test(line)
}

function handleAddToCase() {
  emit('add-to-case', { documentContent: props.result })
}
</script>

<template>
  <el-card shadow="never" class="app-result-card">
    <div class="result-text">
      <div class="result-blocks">
        <div
          v-for="(block, blockIndex) in blocks"
          :key="blockIndex"
          class="result-block"
          :class="{ 'result-block--highlighted': block.highlighted }"
        >
          <p
            v-for="(line, lineIndex) in block.lines"
            :key="lineIndex"
            class="result-line"
            :class="{ 'result-line--sub': isSubLine(line) }"
          >
            {{ line }}
          </p>
        </div>
      </div>
    </div>
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

.result-text {
  white-space: pre-line;
}

.result-blocks {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.result-block {
  padding-left: 0.75rem;
  border-left: 3px solid var(--app-border-color, #e4e7ed);
}

.result-line {
  margin: 0 0 0.35rem 0;
}

.result-line:last-child {
  margin-bottom: 0;
}

.result-line--sub {
  margin-left: 1rem;
}

.result-block--highlighted {
  border-left-color: var(--el-color-primary);
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
