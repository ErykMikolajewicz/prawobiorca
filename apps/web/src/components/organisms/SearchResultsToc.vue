<script setup lang="ts">
import { computed, ref } from 'vue'
import type { AnchorInstance } from 'element-plus'
import SearchResultsTocNode from '@/components/molecules/SearchResultsTocNode.vue'
import { useBreakpoint } from '@/composables/useBreakpoint'
import {
  buildTableOfContents,
  groupResultsByHeader,
  type RegulationSearchResult,
} from '@/utils/searchResults'

const DESKTOP_SCROLL_OFFSET = 16
const MOBILE_SCROLL_OFFSET = 64

const props = defineProps<{ results: Array<RegulationSearchResult> }>()

const emit = defineEmits<{
  (e: 'navigate'): void
}>()

const { isMobile } = useBreakpoint()
const anchor = ref<AnchorInstance>()

const tableOfContents = computed(() => buildTableOfContents(groupResultsByHeader(props.results)))
const hasSummaries = computed(() => props.results.some((result) => result.summary_label))

function onLinkClick(event: MouseEvent) {
  event.preventDefault()
  emit('navigate')
}

function navigateTo(href: string) {
  anchor.value?.scrollTo(href)
  emit('navigate')
}
</script>

<template>
  <nav class="search-results-toc" aria-label="Spis treści">
    <el-anchor
      ref="anchor"
      class="toc-anchor"
      :offset="isMobile ? MOBILE_SCROLL_OFFSET : DESKTOP_SCROLL_OFFSET"
      @click="onLinkClick"
    >
      <SearchResultsTocNode
        v-for="node in tableOfContents"
        :key="node.firstGroupId"
        :node="node"
        @navigate="navigateTo"
      />
    </el-anchor>
    <p v-if="hasSummaries" class="toc-ai-note app-text-secondary">
      Opis artykułu/punktu został wygenerowany przez AI.
    </p>
  </nav>
</template>

<style scoped>
.toc-anchor {
  --el-anchor-font-size: 14px;
  --el-anchor-line-height: 26px;
}

.toc-ai-note {
  position: sticky;
  bottom: 0;
  margin: var(--app-space-md) 0 0;
  padding: var(--app-space-sm) 0;
  background-color: var(--el-drawer-bg-color, var(--el-bg-color-page));
}
</style>
