<script setup lang="ts">
import { computed } from 'vue'
import type { SearchResultElement, SearchResultHighlight } from '@/api/generated/model'

const props = defineProps<{
  result: string
  elements?: Array<SearchResultElement> | null
  highlight?: SearchResultHighlight | null
  score: number
  selectedCaseId?: string
  canAddToCase: boolean
}>()

const emit = defineEmits<{
  (e: 'add-to-case', payload: { documentContent: string }): void
}>()

const SUB_ELEMENT_PATTERN = /^(\d+\)|[a-z]\))\s/

type LineSegment = { text: string; highlighted: boolean }
type ResultLine = { text: string; segments: Array<LineSegment> }
type ResultBlock = { subsection: string | null; lines: Array<ResultLine> }

function createSegments(text: string, elementIndex: number): Array<LineSegment> {
  const highlight = props.highlight

  if (
    !highlight ||
    elementIndex < highlight.start_element ||
    elementIndex > highlight.end_element
  ) {
    return [{ text, highlighted: false }]
  }

  const start = elementIndex === highlight.start_element ? highlight.start_offset : 0
  const end = elementIndex === highlight.end_element ? highlight.end_offset : text.length

  return [
    { text: text.slice(0, start), highlighted: false },
    { text: text.slice(start, end), highlighted: true },
    { text: text.slice(end), highlighted: false },
  ].filter((segment) => segment.text)
}

const blocks = computed<Array<ResultBlock>>(() => {
  const result: Array<ResultBlock> = []

  for (const [elementIndex, element] of (props.elements ?? []).entries()) {
    const lastBlock = result[result.length - 1]
    const line = { text: element.text, segments: createSegments(element.text, elementIndex) }

    if (lastBlock && lastBlock.subsection === element.subsection) {
      lastBlock.lines.push(line)
    } else {
      result.push({ subsection: element.subsection, lines: [line] })
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
  <el-card shadow="hover">
    <div class="result-container">
      <div class="result-text">
        <div v-if="blocks.length" class="result-blocks">
          <div v-for="(block, blockIndex) in blocks" :key="blockIndex" class="result-block">
            <p
              v-for="(line, lineIndex) in block.lines"
              :key="lineIndex"
              class="result-line"
              :class="{ 'result-line--sub': isSubLine(line.text) }"
            >
              <template v-for="(segment, segmentIndex) in line.segments" :key="segmentIndex">
                <mark v-if="segment.highlighted" class="result-highlight">{{ segment.text }}</mark>
                <template v-else>{{ segment.text }}</template>
              </template>
            </p>
          </div>
        </div>
        <span v-else class="result-plain">{{ result }}</span>
      </div>
      <div class="score-column">
        <span class="score-label">Podobieństwo</span>
        <span class="score-value">{{ score.toFixed(3) }}</span>
      </div>
      <div class="actions">
        <el-tooltip
          v-if="canAddToCase"
          :disabled="!!selectedCaseId"
          content="Wybierz bieżącą sprawę, by dodać do niej wyszukany element."
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
.result-container {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.result-text {
  flex: 1;
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

.result-highlight {
  background-color: transparent;
  color: inherit;
  text-decoration: underline;
  text-decoration-color: var(--el-color-primary);
  text-decoration-thickness: 2px;
  text-underline-offset: 3px;
}

.score-column {
  flex-shrink: 0;
  min-width: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary, #909399);
}

.score-label {
  font-size: 0.75em;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 2px;
}

.score-value {
  font-size: 1.1em;
  font-weight: 500;
  color: var(--el-text-color-primary, #303133);
}

.actions {
  flex-shrink: 0;
}

.tooltip-wrapper {
  display: inline-block;
  cursor: not-allowed;
}
</style>
