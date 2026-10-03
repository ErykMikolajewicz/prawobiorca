<script setup lang="ts">
type Props = {
  motionType?: 'search' | 'arrow'
}

withDefaults(defineProps<Props>(), {
  motionType: 'arrow',
})
</script>

<template>
  <span class="icon-btn" aria-hidden="true">
    <span :class="`${motionType}-icon`" aria-hidden="true">
      <slot />
    </span>
  </span>
</template>

<style scoped>
.icon-btn {
  transition: color 0.2s ease;
}

.search-icon :deep(svg),
.arrow-icon :deep(svg) {
  width: 1.5em;
  height: 1.5em;
}
</style>
