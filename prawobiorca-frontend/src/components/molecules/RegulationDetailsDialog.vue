<script setup lang="ts">
import { computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRegulationDetails } from '@/composables/useRegulationDetails'
import { descriptionStatusOptions } from '@/domain/regulations'
import { useAuthStore } from '@/stores/auth'
import type { RegulationRepresentation } from '@/api/generated/model'

type Props = {
  regulation: RegulationRepresentation
  canManage: boolean
}

const props = defineProps<Props>()

const visible = defineModel<boolean>({ required: true })

const emit = defineEmits<{
  (e: 'updated', regulation: RegulationRepresentation): void
  (e: 'deleted', regulationId: string): void
  (e: 'description-generation-started', regulationId: string): void
}>()

const { isAdmin } = storeToRefs(useAuthStore())

const {
  name,
  description,
  isSaving,
  isDeleting,
  isLoadingPreview,
  isGeneratingDescription,
  resetForm,
  save,
  remove,
  generateDescription,
  showPreview,
} = useRegulationDetails()

const createDate = computed(() =>
  new Date(props.regulation.createDate).toLocaleString('pl-PL', {
    dateStyle: 'short',
    timeStyle: 'short',
  }),
)
const canPreview = computed(() => props.regulation.preparationStatus !== 'NOT_STARTED')
const isDescriptionInProgress = computed(() => props.regulation.descriptionStatus === 'IN_PROGRESS')
const canGenerateDescription = computed(
  () =>
    isAdmin.value &&
    props.canManage &&
    props.regulation.preparationStatus === 'PREPARED' &&
    !isDescriptionInProgress.value,
)
const descriptionStatus = computed(() => {
  const status = props.regulation.descriptionStatus
  if (status === 'IN_PROGRESS' || status === 'FAILED') {
    return descriptionStatusOptions[status]
  }
  return undefined
})

watch(
  visible,
  (isVisible) => {
    if (isVisible) {
      resetForm(props.regulation)
    }
  },
  { immediate: true },
)

watch(
  () => props.regulation.description,
  (newDescription) => {
    description.value = newDescription ?? ''
  },
)

function closeDialog() {
  visible.value = false
}

async function handleSave() {
  const regulation = await save(props.regulation.id)
  if (!regulation) {
    return
  }

  emit('updated', regulation)
}

async function handleDelete() {
  const isDeleted = await remove(props.regulation.id)
  if (!isDeleted) {
    return
  }

  emit('deleted', props.regulation.id)
  closeDialog()
}

async function handleGenerateDescription() {
  if (await generateDescription(props.regulation.id)) {
    emit('description-generation-started', props.regulation.id)
  }
}

function handlePreview() {
  showPreview(props.regulation.id)
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
          :rows="6"
          maxlength="1000"
          show-word-limit
          placeholder="Opis regulacji"
          :disabled="isDescriptionInProgress"
        />
        <span v-else class="regulation-description">{{
          regulation.description || 'Brak opisu'
        }}</span>

        <div v-if="canManage && isAdmin" class="description-generation">
          <el-tag
            v-if="descriptionStatus"
            size="small"
            effect="plain"
            :type="descriptionStatus.tagType"
            class="app-badge"
          >
            {{ descriptionStatus.label }}
          </el-tag>
          <el-button
            v-if="canGenerateDescription"
            size="small"
            :loading="isGeneratingDescription"
            @click="handleGenerateDescription"
          >
            Wygeneruj opis przez AI
          </el-button>
        </div>
      </el-form-item>

      <el-form-item label="Data dodania:" label-position="left">
        <span>{{ createDate }}</span>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button v-if="canPreview" :loading="isLoadingPreview" @click="handlePreview">
          Pokaż podgląd
        </el-button>

        <div class="dialog-footer-actions">
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

.description-generation {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--app-space-sm);
  width: 100%;
  margin-top: var(--app-space-sm);
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  gap: var(--app-space-sm);
}

.dialog-footer-actions {
  display: flex;
  gap: var(--app-space-sm);
  margin-left: auto;
}
</style>
