<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  deletePublicRegulation,
  getPublicRegulationDownloadUrl,
  updatePublicRegulation,
} from '@/api/generated/endpoints/regulations/regulations'
import {
  deleteUserRegulation,
  getUserRegulationDownloadUrl,
  updateUserRegulation,
} from '@/api/generated/endpoints/user-regulations/user-regulations'
import { showApiError } from '@/utils/error'
import { toBrowserStorageUrl } from '@/utils/storage'
import type { RegulationRepresentation } from '@/api/generated/model'
import type { RegulationScope } from '@/domain/regulations'

type Props = {
  regulation: RegulationRepresentation
  target: RegulationScope
  canManage: boolean
}

const props = defineProps<Props>()

const visible = defineModel<boolean>({ required: true })

const emit = defineEmits<{
  (e: 'updated', regulation: RegulationRepresentation): void
  (e: 'deleted', regulationId: string): void
}>()

const name = ref('')
const description = ref('')
const isSaving = ref(false)
const isDeleting = ref(false)
const isLoadingPreview = ref(false)

const createDate = computed(() => new Date(props.regulation.createDate).toLocaleString('pl-PL'))
const canPreview = computed(() => props.regulation.preparationStatus !== 'NOT_STARTED')

const updateRegulation = props.target === 'public' ? updatePublicRegulation : updateUserRegulation
const deleteRegulation = props.target === 'public' ? deletePublicRegulation : deleteUserRegulation
const getRegulationDownloadUrl =
  props.target === 'public' ? getPublicRegulationDownloadUrl : getUserRegulationDownloadUrl

watch(visible, (isVisible) => {
  if (isVisible) {
    name.value = props.regulation.presentationName
    description.value = props.regulation.description ?? ''
  }
})

function closeDialog() {
  visible.value = false
}

async function handleSave() {
  if (!name.value.trim()) {
    ElMessage.warning('Podaj nazwę regulacji.')
    return
  }

  try {
    isSaving.value = true
    const regulation = await updateRegulation(props.regulation.id, {
      name: name.value.trim(),
      description: description.value.trim() || null,
    })
    ElMessage.success('Regulacja została zaktualizowana')
    emit('updated', regulation)
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się zaktualizować regulacji' })
  } finally {
    isSaving.value = false
  }
}

async function handleDelete() {
  try {
    isDeleting.value = true
    await deleteRegulation(props.regulation.id)
    ElMessage.success('Regulacja została usunięta')
    emit('deleted', props.regulation.id)
    closeDialog()
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się usunąć regulacji' })
  } finally {
    isDeleting.value = false
  }
}

async function showPreview() {
  const previewWindow = window.open('', '_blank')
  try {
    isLoadingPreview.value = true
    const previewUrl = toBrowserStorageUrl(await getRegulationDownloadUrl(props.regulation.id))
    if (previewWindow) {
      previewWindow.opener = null
      previewWindow.location.href = previewUrl
    }
  } catch (error) {
    previewWindow?.close()
    showApiError(error, { defaultMessage: 'Nie udało się pobrać podglądu pliku' })
  } finally {
    isLoadingPreview.value = false
  }
}
</script>

<template>
  <el-dialog v-model="visible" title="Szczegóły regulacji" width="min(720px, 92vw)" append-to-body>
    <el-form label-position="top" @submit.prevent="handleSave">
      <el-form-item label="Nazwa:">
        <el-input v-if="canManage" v-model="name" placeholder="Nazwa regulacji" />
        <span v-else>{{ regulation.presentationName }}</span>
      </el-form-item>

      <el-form-item label="Opis:">
        <el-input
          v-if="canManage"
          v-model="description"
          type="textarea"
          :rows="4"
          maxlength="1000"
          show-word-limit
          placeholder="Opis regulacji"
        />
        <span v-else class="regulation-description">{{
          regulation.description || 'Brak opisu'
        }}</span>
      </el-form-item>

      <el-form-item label="Data dodania:">
        <span>{{ createDate }}</span>
      </el-form-item>
    </el-form>

    <el-button v-if="canPreview" :loading="isLoadingPreview" @click="showPreview">
      Pokaż podgląd
    </el-button>

    <template #footer>
      <div class="dialog-footer">
        <el-popconfirm
          v-if="canManage"
          title="Czy na pewno chcesz usunąć tę regulację?"
          confirm-button-text="Tak"
          cancel-button-text="Nie"
          @confirm="handleDelete"
        >
          <template #reference>
            <el-button type="danger" plain :loading="isDeleting">Usuń</el-button>
          </template>
        </el-popconfirm>

        <div class="dialog-footer-actions">
          <el-button @click="closeDialog">Zamknij</el-button>
          <el-button v-if="canManage" type="primary" :loading="isSaving" @click="handleSave">
            Zapisz
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.regulation-description {
  white-space: pre-wrap;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.dialog-footer-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}
</style>
