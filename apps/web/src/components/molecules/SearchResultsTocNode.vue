<script setup lang="ts">
import type { TocNode } from '@/utils/searchResults'

const props = defineProps<{ node: TocNode }>()

const emit = defineEmits<{
  (e: 'navigate', href: string): void
}>()

function navigateToFirstGroup() {
  emit('navigate', `#${props.node.firstGroupId}`)
}
</script>

<template>
  <el-anchor-link v-if="node.groupId" :href="`#${node.groupId}`" :title="node.title">
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
</style>
