<script setup lang="ts">
import { onBeforeMount, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'

import AppLayout from '@/components/templates/AppLayout.vue'

import { getUsageTariff, updateUsageTariff } from '@/api/generated/endpoints/usage/usage'

import type { UsageTariffData } from '@/api/generated/model'

type TariffField = { key: keyof UsageTariffData; label: string }

const PRICE_FIELDS: TariffField[] = [
  { key: 'semanticSearchPrice', label: 'Wyszukiwanie semantyczne' },
  { key: 'applicationGenerationPrice', label: 'Generowanie wniosku' },
  { key: 'regulationPreparationPrice', label: 'Przygotowanie prywatnego dokumentu' },
]

const LIMIT_FIELDS: TariffField[] = [
  { key: 'accountDailyLimit', label: 'Konto użytkownika' },
  { key: 'anonymousIpDailyLimit', label: 'Gość – jeden adres IP' },
  { key: 'anonymousTotalDailyLimit', label: 'Wszyscy goście łącznie' },
]

const SECTIONS = [
  { title: 'Ceny operacji', fields: PRICE_FIELDS },
  { title: 'Dzienne budżety', fields: LIMIT_FIELDS },
]

const tariff = ref<UsageTariffData | null>(null)
const isLoading = ref(false)
const isSaving = ref(false)

async function loadTariff() {
  isLoading.value = true
  try {
    tariff.value = await getUsageTariff()
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się pobrać cennika.' })
  } finally {
    isLoading.value = false
  }
}

async function handleSubmit() {
  if (!tariff.value) {
    return
  }
  isSaving.value = true
  try {
    await updateUsageTariff(tariff.value)
    ElMessage.success('Zmiany zostały zapisane.')
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się zapisać zmian.' })
  } finally {
    isSaving.value = false
  }
}

onBeforeMount(loadTariff)
</script>

<template>
  <AppLayout>
    <div class="page-header">
      <h1 class="page-title">Limity i cennik</h1>
    </div>

    <div v-loading="isLoading" class="tariff-page">
      <el-form v-if="tariff" label-position="top" @submit.prevent="handleSubmit">
        <el-card
          v-for="section in SECTIONS"
          :key="section.title"
          shadow="never"
          class="app-card tariff-section"
        >
          <template #header>{{ section.title }}</template>
          <el-form-item v-for="field in section.fields" :key="field.key" :label="field.label">
            <el-input-number
              v-model="tariff[field.key]"
              :min="0"
              :precision="2"
              :step="0.01"
              value-on-clear="min"
              controls-position="right"
            />
            <span class="currency">zł</span>
          </el-form-item>
        </el-card>

        <el-button type="primary" native-type="submit" :loading="isSaving">Zapisz</el-button>
      </el-form>
      <el-empty v-else-if="!isLoading" description="Nie udało się pobrać cennika." />
    </div>
  </AppLayout>
</template>

<style scoped>
.tariff-page {
  min-height: 120px;
  max-width: 480px;
}

.tariff-section {
  margin-bottom: var(--app-space-lg);
}

.currency {
  margin-left: var(--app-space-sm);
}
</style>
