<script setup lang="ts">
import { useBreakpoint } from '@/composables/useBreakpoint'
import type { TocNode } from '@/utils/searchResults'

const props = defineProps<{ node: TocNode }>()

const emit = defineEmits<{
  (e: 'navigate', href: string): void
}>()

const { isMobile } = useBreakpoint()

function navigateToFirstGroup() {
  emit('navigate', `#${props.node.firstGroupId}`)
}
</script>

<template>
  <el-anchor-link v-if="node.groupId" :href="`#${node.groupId}`">
    <el-tooltip
      :disabled="isMobile || !node.summary"
      :content="node.summary"
      placement="left"
      :show-after="300"
    >
      <span>
        {{ node.title }}
        <span v-if="node.summaryLabel" class="toc-summary-label">· {{ node.summaryLabel }}</span>
      </span>
    </el-tooltip>
    <template v-if="node.children.length" #sub-link>
      <SearchResultsTocNode
        v-for="child in node.children"
        :key="child.firstGroupId"
        :node="child"
        @navigate="(href) => emit('navigate', href)"
      />
    </template>
  </el-anchor-link>
  <div v-else class="el-anchor__item">
    <a
      class="el-anchor__link toc-chapter"
      :href="`#${node.firstGroupId}`"
      @click.prevent="navigateToFirstGroup"
    >
      {{ node.title }}
    </a>
    <div class="el-anchor__list">
      <SearchResultsTocNode
        v-for="child in node.children"
        :key="child.firstGroupId"
        :node="child"
        @navigate="(href) => emit('navigate', href)"
      />
    </div>
  </div>
</template>

<style scoped>
.toc-chapter {
  font-weight: 600;
}

.toc-summary-label {
  color: var(--el-text-color-secondary);
}
</style>
