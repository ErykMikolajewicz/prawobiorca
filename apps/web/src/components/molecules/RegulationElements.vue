<script setup lang="ts">
import { computed } from 'vue'
import type { SearchResultElement, SearchResultHighlight } from '@/api/generated/model'

const props = defineProps<{
  elements: Array<SearchResultElement>
  highlight?: SearchResultHighlight | null
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
</script>

<template>
  <div class="result-blocks">
    <div
      v-for="(block, blockIndex) in blocks"
      :key="blockIndex"
      class="result-block"
      :class="{ 'is-highlighted': block.highlighted }"
    >
      <p
        v-for="(line, lineIndex) in block.lines"
        :key="lineIndex"
        class="result-line"
        :class="{ 'is-sub': isSubLine(line) }"
      >
        {{ line }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.result-blocks {
  display: flex;
  flex-direction: column;
  white-space: pre-line;
}

.result-block {
  padding-left: var(--app-space-md);
  border-left: 3px solid transparent;
}

.result-block + .result-block {
  padding-top: var(--app-space-xs);
}

.result-line {
  margin: 0 0 var(--app-space-xs) 0;
}

.result-line:last-child {
  margin-bottom: 0;
}

.result-line.is-sub {
  margin-left: var(--app-space-lg);
}

.result-block.is-highlighted {
  border-left-color: var(--el-color-primary);
}
</style>
