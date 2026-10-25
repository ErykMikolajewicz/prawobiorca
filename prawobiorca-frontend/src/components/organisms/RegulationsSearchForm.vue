<script setup lang="ts">
import { reactive } from 'vue'

import SearchThresholdControl from '@/components/molecules/SearchThresholdControl.vue'
import { useBreakpoint } from '@/composables/useBreakpoint'
import type { RegulationsSearchParams } from '@/domain/regulations'

const props = defineProps<{
  searchParams: RegulationsSearchParams
  canUseAdvancedThreshold: boolean
}>()

const emit = defineEmits<{
  (e: 'search', searchParams: RegulationsSearchParams): void
}>()

const { isMobile } = useBreakpoint()

const searchParams = reactive<RegulationsSearchParams>({ ...props.searchParams })

function onSubmit() {
  const query = searchParams.query.trim()
  emit('search', {
    ...searchParams,
    query,
    orderBy: query ? searchParams.orderBy : 'name',
  })
}
</script>

<template>
  <el-form :label-position="isMobile ? 'top' : 'right'" @submit.prevent="onSubmit">
    <el-form-item label="Czego szukasz?">
      <el-input
        v-model="searchParams.query"
        placeholder="Opisz sprawę, np. przeniesienie na inny kierunek studiów"
        clearable
        @clear="onSubmit"
      />
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
        <el-form-item label="Kolejność:">
          <el-radio-group v-model="searchParams.orderBy" @change="onSubmit">
            <el-radio-button value="name">Alfabetycznie</el-radio-button>
            <el-radio-button value="score" :disabled="!searchParams.query.trim()">
              Wg trafności
            </el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-col>
    </el-row>
    <el-form-item>
      <el-button native-type="submit">Szukaj</el-button>
    </el-form-item>
  </el-form>
</template>
