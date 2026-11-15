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
  </nav>
</template>
