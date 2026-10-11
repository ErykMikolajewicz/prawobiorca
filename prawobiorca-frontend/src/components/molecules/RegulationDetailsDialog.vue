<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRegulationDetails } from '@/composables/useRegulationDetails'
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

const {
  name,
  description,
  isSaving,
  isDeleting,
  isLoadingPreview,
  resetForm,
  save,
  remove,
  showPreview,
} = useRegulationDetails(props.target)

const createDate = computed(() =>
  new Date(props.regulation.createDate).toLocaleString('pl-PL', {
    dateStyle: 'short',
    timeStyle: 'short',
  }),
)
const canPreview = computed(() => props.regulation.preparationStatus !== 'NOT_STARTED')

watch(
  visible,
  (isVisible) => {
    if (isVisible) {
      resetForm(props.regulation)
    }
  },
  { immediate: true },
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
        />
        <span v-else class="regulation-description">{{
          regulation.description || 'Brak opisu'
        }}</span>
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
