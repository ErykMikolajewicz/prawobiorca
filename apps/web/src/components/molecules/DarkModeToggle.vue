<script setup lang="ts">
import { useDarkMode } from '@/composables/useDarkMode'
import LightModeRoundedIcon from '@iconify-vue/material-symbols/light-mode-rounded'
import DarkModeRoundedIcon from '@iconify-vue/material-symbols/dark-mode-rounded'

const { isDark, toggleDark } = useDarkMode()
</script>

<template>
  <button
    class="icon-btn"
    type="button"
    :title="isDark ? 'Przełącz na tryb jasny' : 'Przełącz na tryb ciemny'"
    @click="toggleDark"
  >
    <LightModeRoundedIcon v-if="isDark" />
    <DarkModeRoundedIcon v-else />
  </button>
</template>
