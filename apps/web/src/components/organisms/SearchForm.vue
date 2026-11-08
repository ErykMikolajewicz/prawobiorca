<script setup lang="ts">
import { reactive } from 'vue'

import SearchThresholdControl from '@/components/molecules/SearchThresholdControl.vue'
import { useBreakpoint } from '@/composables/useBreakpoint'
import type { SearchRegulationDocumentsParams } from '@/api/generated/model'

const props = defineProps<{
  searchParams: SearchRegulationDocumentsParams
  canUseAdvancedThreshold: boolean
}>()

const emit = defineEmits<{
  (e: 'search', searchConfig: SearchRegulationDocumentsParams): void
}>()

const { isMobile } = useBreakpoint()

const searchParams = reactive<SearchRegulationDocumentsParams>({ ...props.searchParams })

function onSubmit() {
  if (searchParams.query.trim()) {
    emit('search', { ...searchParams })
  }
}
</script>

<template>
  <el-form :label-position="isMobile ? 'top' : 'right'" @submit.prevent="onSubmit">
    <el-form-item label="Twoje zapytanie:">
      <el-input v-model="searchParams.query" placeholder="Wpisz treść..." clearable required />
    </el-form-item>
    <el-row :gutter="20">
      <el-col :span="12" :xs="24">
        <el-form-item label="Poziom istotności:">
          <SearchThresholdControl
            v-model="searchParams.threshold"
            :can-use-advanced="canUseAdvancedThreshold"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12" :xs="24">
        <el-form-item label="Maksymalna liczba wyników:">
          <el-input-number
            v-model="searchParams.limit"
            :min="1"
            :step="1"
            placeholder="Brak limitu"
            class="limit-input"
          />
        </el-form-item>
      </el-col>
    </el-row>
    <el-form-item label="Kolejność wyników:">
      <el-radio-group v-model="searchParams.order_by" @change="onSubmit">
        <el-radio-button value="score">Wg trafności</el-radio-button>
        <el-radio-button value="document">Wg aktu prawnego</el-radio-button>
      </el-radio-group>
    </el-form-item>
    <el-form-item>
      <el-button native-type="submit">Przeszukaj</el-button>
    </el-form-item>
  </el-form>
</template>

<style scoped>
.limit-input {
  width: 100%;
}
</style>
