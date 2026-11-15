<script setup lang="ts">
import { computed } from 'vue'
import SearchResultItem from '@/components/molecules/SearchResultItem.vue'
import type { SearchResultElement, SearchResultHighlight } from '@/api/generated/model'
import { groupResultsByHeader, type RegulationSearchResult } from '@/utils/searchResults'

const props = defineProps<{
  results: Array<RegulationSearchResult>
  selectedCaseId?: string
  canAddToCase: boolean
  query: string
}>()

type AddToCasePayload = {
  documentContent: string
  header: string | null
  elements: Array<SearchResultElement>
  highlight: SearchResultHighlight | null
}

const emit = defineEmits<{
  (e: 'add-to-case', payload: AddToCasePayload): void
}>()

function onAddToCase(payload: AddToCasePayload) {
  emit('add-to-case', payload)
}

const groupedResults = computed(() => groupResultsByHeader(props.results))
</script>

<template>
  <div class="search-results">
    <el-divider />

    <div v-if="results.length">
      <h2 v-if="query" class="section-title">Wyniki:</h2>
      <div v-for="group in groupedResults" :id="group.id" :key="group.id" class="result-group">
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
          @add-to-case="(payload) => onAddToCase({ ...payload, header: group.header })"
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
  margin-bottom: var(--app-space-xl);
}

.result-group-header {
  margin: 0 0 var(--app-space-sm) 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
</style>
