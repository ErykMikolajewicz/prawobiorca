<script setup lang="ts">
import { computed, ref } from 'vue'
import SearchResultItem from '@/components/molecules/SearchResultItem.vue'
import type { searchResult } from '@/types/api/search.ts'

const props = defineProps<{
  results: Array<searchResult>
  selectedCaseId?: string
  query: string
}>()

const emit = defineEmits<{
  (e: 'add-to-case', payload: { documentContent: string }): void
}>()

const showHighlight = ref(true)

const onAddToCase = (payload: { documentContent: string }) => {
  emit('add-to-case', payload)
}

type ResultGroup = {
  header: string | null
  items: Array<searchResult>
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
      <div class="results-header">
        <h2>Wyniki:</h2>
        <el-switch v-model="showHighlight" active-text="Podświetlaj najlepszy fragment" />
      </div>
      <div v-for="(group, groupIndex) in groupedResults" :key="groupIndex" class="result-group">
        <h3 class="result-group-header">{{ group.header }}</h3>
        <SearchResultItem
          v-for="{ id, text, score, elements, highlight } in group.items"
          :key="id"
          :result="text"
          :elements="elements"
          :highlight="showHighlight ? highlight : null"
          :score="score"
          :selected-case-id="selectedCaseId"
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
.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
}

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
