<script setup lang="ts">
import { watch } from 'vue'
import FileSelectButton from '@/components/atoms/FileSelectButton.vue'
import { useRegulationUpload, regulationTypeOptions } from '@/composables/useRegulationUpload'
import type { RegulationRepresentation } from '@/api/generated/model'
import type { uploadTarget } from '@/composables/useRegulationUpload'

type Props = {
  modelValue: boolean
  isAdmin: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'created', regulation: RegulationRepresentation, target: uploadTarget): void
}>()

const {
  selectedFile,
  presentationName,
  selectedRegulationType,
  target,
  isSubmitting,
  resetForm,
  setFile,
  submit,
} = useRegulationUpload()

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      resetForm()
    }
  },
)

function closeDialog() {
  emit('update:modelValue', false)
}

async function handleSubmit() {
  const result = await submit()
  if (!result) {
    return
  }

  emit('created', result.regulation, result.target)
  closeDialog()
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="Dodaj plik"
    width="min(480px, 92vw)"
    @update:model-value="(value: boolean) => emit('update:modelValue', value)"
  >
    <el-form label-position="top" @submit.prevent="handleSubmit">
      <el-form-item label="Plik:">
        <FileSelectButton :model-value="selectedFile" @update:model-value="setFile" />
      </el-form-item>

      <el-form-item label="Nazwa pliku:">
        <el-input v-model="presentationName" placeholder="Nazwa pliku" />
      </el-form-item>

      <el-form-item label="Etykieta (opcjonalnie):">
        <el-select v-model="selectedRegulationType" clearable placeholder="Wybierz etykietę">
          <el-option
            v-for="option in regulationTypeOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item v-if="isAdmin" label="Widoczność pliku:">
        <el-radio-group v-model="target">
          <el-radio value="user">Plik użytkownika (prywatny)</el-radio>
          <el-radio value="public">Plik publiczny</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="closeDialog">Anuluj</el-button>
      <el-button type="primary" :loading="isSubmitting" @click="handleSubmit">Dodaj</el-button>
    </template>
  </el-dialog>
</template>
