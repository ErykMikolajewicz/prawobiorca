<script setup lang="ts">
import { computed } from 'vue'
import SearchResultItem from '@/components/molecules/SearchResultItem.vue'
import type { SearchResult } from '@/api/generated/model'

const props = defineProps<{
  results: Array<SearchResult>
  selectedCaseId?: string
  canAddToCase: boolean
  query: string
}>()

const emit = defineEmits<{
  (e: 'add-to-case', payload: { documentContent: string }): void
}>()

function onAddToCase(payload: { documentContent: string }) {
  emit('add-to-case', payload)
}

type ResultGroup = {
  header: string | null
  items: Array<SearchResult>
}

const groupedResults = computed<Array<ResultGroup>>(() => {
  const groups: Array<ResultGroup> = []

  for (const result of props.results) {
    const lastGroup = groups[groups.length - 1]

    if (lastGroup && lastGroup.header === result.header) {
      lastGroup.items.push(result)
    } else {
      groups.push({ header: result.header, items: [result] })
    }
  }

  return groups
})
</script>

<template>
  <div class="search-results">
    <el-divider />

    <div v-if="results.length">
      <h2>Wyniki:</h2>
      <div v-for="(group, groupIndex) in groupedResults" :key="groupIndex" class="result-group">
        <h3 class="result-group-header">{{ group.header }}</h3>
        <SearchResultItem
          v-for="{ id, text, score, elements, highlight } in group.items"
          :key="id"
          :result="text"
          :elements="elements"
          :highlight="highlight"
          :score="score"
          :selected-case-id="selectedCaseId"
          :can-add-to-case="canAddToCase"
          @add-to-case="onAddToCase"
        />
      </div>
    </div>
    <div v-else-if="query">
      <p>Brak wyników dla zapytania: "{{ query }}"</p>
    </div>
  </div>
</template>

<style scoped>
.result-group {
  margin-bottom: 1.5rem;
}

.result-group-header {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--el-text-color-primary, #303133);
}
</style>
