<script setup lang="ts">
import { computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import FileSelectButton from '@/components/atoms/FileSelectButton.vue'
import { useRegulationUpload } from '@/composables/useRegulationUpload'
import { useOrganizationsStore } from '@/stores/organizations'
import { regulationTypeOptions, type RegulationScope } from '@/domain/regulations'
import type { RegulationRepresentation } from '@/api/generated/model'

type Props = {
  isAdmin: boolean
}

defineProps<Props>()

const visible = defineModel<boolean>({ required: true })

const emit = defineEmits<{
  (e: 'created', regulation: RegulationRepresentation, target: RegulationScope): void
}>()

const {
  selectedFile,
  presentationName,
  selectedRegulationType,
  target,
  selectedOrganizationId,
  selectedSuborganizationId,
  isSubmitting,
  resetForm,
  setFile,
  submit,
} = useRegulationUpload()

const { organizations } = storeToRefs(useOrganizationsStore())

const suborganizations = computed(
  () =>
    organizations.value.find((organization) => organization.id === selectedOrganizationId.value)
      ?.suborganizations ?? [],
)

watch(selectedOrganizationId, () => {
  selectedSuborganizationId.value = ''
})

watch(visible, (isVisible) => {
  if (isVisible) {
    resetForm()
  }
})

function closeDialog() {
  visible.value = false
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
  <el-dialog v-model="visible" title="Dodaj plik" width="min(480px, 92vw)">
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

      <template v-if="isAdmin && target === 'public'">
        <el-form-item label="Organizacja (opcjonalnie):">
          <el-select v-model="selectedOrganizationId" clearable placeholder="Ogólny">
            <el-option
              v-for="organization in organizations"
              :key="organization.id"
              :label="organization.name"
              :value="organization.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="Podorganizacja (opcjonalnie):">
          <el-select
            v-model="selectedSuborganizationId"
            :disabled="!selectedOrganizationId"
            clearable
            placeholder="Wszystkie podorganizacje"
          >
            <el-option
              v-for="suborganization in suborganizations"
              :key="suborganization.id"
              :label="suborganization.name"
              :value="suborganization.id"
            />
          </el-select>
        </el-form-item>
      </template>
    </el-form>

    <template #footer>
      <el-button @click="closeDialog">Anuluj</el-button>
      <el-button type="primary" :loading="isSubmitting" @click="handleSubmit">Dodaj</el-button>
    </template>
  </el-dialog>
</template>
