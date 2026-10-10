<script setup lang="ts">
import { computed, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'

import AppLayout from '@/components/templates/AppLayout.vue'
import OrganizationsList from '@/components/organisms/OrganizationsList.vue'
import OrganizationFormDialog from '@/components/molecules/OrganizationFormDialog.vue'

import {
  addOrganization,
  addSuborganization,
  deleteOrganization,
  deleteSuborganization,
  updateOrganization,
  updateSuborganization,
} from '@/api/generated/endpoints/organizations/organizations'
import { useOrganizationsStore } from '@/stores/organizations'

import type { OrganizationData, SuborganizationData } from '@/api/generated/model'

type DialogTarget =
  | { kind: 'add-organization' }
  | { kind: 'edit-organization'; organization: OrganizationData }
  | { kind: 'add-suborganization'; organizationId: string }
  | { kind: 'edit-suborganization'; suborganization: SuborganizationData }

const organizationsStore = useOrganizationsStore()
const { organizations } = storeToRefs(organizationsStore)

const dialogTarget = ref<DialogTarget>({ kind: 'add-organization' })
const isDialogVisible = ref(false)
const isSubmitting = ref(false)

const DIALOG_TITLES: Record<DialogTarget['kind'], string> = {
  'add-organization': 'Dodaj organizację',
  'edit-organization': 'Edytuj organizację',
  'add-suborganization': 'Dodaj podorganizację',
  'edit-suborganization': 'Edytuj podorganizację',
}

const dialogTitle = computed(() => DIALOG_TITLES[dialogTarget.value.kind])

const isOrganizationDialog = computed(
  () =>
    dialogTarget.value.kind === 'add-organization' ||
    dialogTarget.value.kind === 'edit-organization',
)

const initialName = computed(() => {
  if (dialogTarget.value.kind === 'edit-organization') {
    return dialogTarget.value.organization.name
  }
  if (dialogTarget.value.kind === 'edit-suborganization') {
    return dialogTarget.value.suborganization.name
  }
  return ''
})

const initialShortName = computed(() =>
  dialogTarget.value.kind === 'edit-organization' ? dialogTarget.value.organization.shortName : '',
)

function openDialog(target: DialogTarget) {
  dialogTarget.value = target
  isDialogVisible.value = true
}

async function saveDialog(target: DialogTarget, name: string, shortName: string) {
  switch (target.kind) {
    case 'add-organization':
      await addOrganization({ name, shortName })
      return
    case 'edit-organization':
      await updateOrganization(target.organization.id, { name, shortName })
      return
    case 'add-suborganization':
      await addSuborganization(target.organizationId, { name })
      return
    case 'edit-suborganization':
      await updateSuborganization(target.suborganization.id, { name })
      return
  }
}

async function handleSubmit(name: string, shortName: string) {
  isSubmitting.value = true
  try {
    await saveDialog(dialogTarget.value, name, shortName)
    isDialogVisible.value = false
    ElMessage.success('Zmiany zostały zapisane.')
    await organizationsStore.load()
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się zapisać zmian.' })
  } finally {
    isSubmitting.value = false
  }
}

async function handleDeleteOrganization(organizationId: string) {
  try {
    await deleteOrganization(organizationId)
    ElMessage.success('Organizacja została usunięta.')
    await organizationsStore.load()
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się usunąć organizacji.' })
  }
}

async function handleDeleteSuborganization(suborganizationId: string) {
  try {
    await deleteSuborganization(suborganizationId)
    ElMessage.success('Podorganizacja została usunięta.')
    await organizationsStore.load()
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się usunąć podorganizacji.' })
  }
}
</script>

<template>
  <AppLayout>
    <div class="page-header">
      <h1>Organizacje</h1>
      <el-button type="primary" @click="openDialog({ kind: 'add-organization' })">
        Dodaj organizację
      </el-button>
    </div>

    <OrganizationsList
      :organizations="organizations"
      @edit-organization="openDialog({ kind: 'edit-organization', organization: $event })"
      @delete-organization="handleDeleteOrganization"
      @add-suborganization="openDialog({ kind: 'add-suborganization', organizationId: $event })"
      @edit-suborganization="openDialog({ kind: 'edit-suborganization', suborganization: $event })"
      @delete-suborganization="handleDeleteSuborganization"
    />

    <OrganizationFormDialog
      v-model="isDialogVisible"
      :title="dialogTitle"
      :with-short-name="isOrganizationDialog"
      :initial-name="initialName"
      :initial-short-name="initialShortName"
      :submitting="isSubmitting"
      @submit="handleSubmit"
    />
  </AppLayout>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}
</style>
