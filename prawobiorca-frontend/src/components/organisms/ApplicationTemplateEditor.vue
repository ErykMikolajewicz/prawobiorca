<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'
import { downloadApplicationTemplate } from '@/api/applicationTemplates'
import ApplicationTemplateStatusBadge from '@/components/atoms/ApplicationTemplateStatusBadge.vue'
import ApplicationTemplateFieldEditor from '@/components/molecules/ApplicationTemplateFieldEditor.vue'
import {
  deleteApplicationTemplate,
  publishApplicationTemplate,
  unpublishApplicationTemplate,
  updateApplicationTemplate,
} from '@/api/generated/endpoints/application-templates/application-templates'
import { toEditableField, type EditableTemplateField } from '@/domain/applicationTemplates'
import type {
  ApplicationTemplateDetailsData,
  ApplicationTemplateRepresentation,
} from '@/api/generated/model'

type Props = {
  template: ApplicationTemplateRepresentation
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'updated', template: ApplicationTemplateRepresentation): void
  (e: 'deleted', templateId: string): void
}>()

const form = reactive({
  name: '',
  instructions: '',
  fields: [] as Array<EditableTemplateField>,
})

const isSaving = ref(false)
const isPublishing = ref(false)
const isDeleting = ref(false)
const isDownloading = ref(false)

const isDraft = computed(() => props.template.status === 'DRAFT')
const isPublished = computed(() => props.template.status === 'PUBLISHED')
const isNotUploaded = computed(() => props.template.status === 'NOT_UPLOADED')

watch(
  () => props.template,
  (template) => {
    form.name = template.name
    form.instructions = template.instructions ?? ''
    form.fields = template.fields.map(toEditableField)
  },
  { immediate: true },
)

function toDetailsData(): ApplicationTemplateDetailsData {
  return {
    name: form.name.trim(),
    instructions: form.instructions.trim() || null,
    fields: form.fields.map((field) => ({
      ...field,
      defaultValue: field.defaultValue || null,
      pattern: field.pattern || null,
    })),
  }
}

async function save(): Promise<boolean> {
  try {
    emit('updated', await updateApplicationTemplate(props.template.id, toDetailsData()))
    return true
  } catch (error) {
    showApiError(error, {
      defaultMessage:
        'Nie udało się zapisać szablonu. Sprawdź nazwę, regexy, opcje list i wartości domyślne.',
    })
    return false
  }
}

async function handleSave() {
  isSaving.value = true
  try {
    if (await save()) {
      ElMessage.success('Szablon został zapisany.')
    }
  } finally {
    isSaving.value = false
  }
}

async function handlePublish() {
  isPublishing.value = true
  try {
    if (!(await save())) {
      return
    }
    emit('updated', await publishApplicationTemplate(props.template.id))
    ElMessage.success('Szablon został opublikowany.')
  } catch (error) {
    showApiError(error, {
      conflictMessage: 'Uzupełnij instrukcje dla AI przed publikacją.',
      defaultMessage: 'Nie udało się opublikować szablonu.',
    })
  } finally {
    isPublishing.value = false
  }
}

async function handleUnpublish() {
  isPublishing.value = true
  try {
    emit('updated', await unpublishApplicationTemplate(props.template.id))
    ElMessage.success('Publikacja szablonu została wycofana.')
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się wycofać publikacji szablonu.' })
  } finally {
    isPublishing.value = false
  }
}

async function handleDownload() {
  isDownloading.value = true
  try {
    await downloadApplicationTemplate(props.template.id)
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się pobrać szablonu.' })
  } finally {
    isDownloading.value = false
  }
}

async function handleDelete() {
  isDeleting.value = true
  try {
    await deleteApplicationTemplate(props.template.id)
    ElMessage.success('Szablon został usunięty.')
    emit('deleted', props.template.id)
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się usunąć szablonu.' })
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <div class="template-editor">
    <div class="editor-header">
      <h2 class="section-title">{{ template.name }}</h2>
      <ApplicationTemplateStatusBadge :status="template.status" />
      <el-button
        v-if="!isNotUploaded"
        class="download-button"
        :loading="isDownloading"
        @click="handleDownload"
      >
        Pobierz szablon
      </el-button>
    </div>

    <el-alert
      v-if="isNotUploaded"
      type="error"
      show-icon
      :closable="false"
      title="Plik szablonu nie został wczytany. Usuń szablon i dodaj go ponownie."
    />
    <el-alert
      v-else-if="isPublished"
      type="info"
      show-icon
      :closable="false"
      title="Szablon jest opublikowany. Wycofaj publikację, aby go edytować."
    />

    <el-form
      v-if="!isNotUploaded"
      label-position="top"
      :disabled="!isDraft"
      @submit.prevent="handleSave"
    >
      <el-row :gutter="24">
        <el-col :span="12" :xs="24">
          <el-form-item label="Nazwa:">
            <el-input v-model="form.name" />
          </el-form-item>

          <el-form-item label="Instrukcje dla AI:">
            <el-input
              v-model="form.instructions"
              type="textarea"
              :rows="8"
              placeholder="np. Sporządź wniosek do Dziekana o przedłużenie terminu złożenia pracy dyplomowej. Podziel treść na 3 akapity: ..."
            />
          </el-form-item>
        </el-col>

        <el-col :span="12" :xs="24">
          <h3 class="fields-title">Pola formularza</h3>
          <el-collapse v-if="form.fields.length" class="fields-collapse">
            <ApplicationTemplateFieldEditor
              v-for="(field, index) in form.fields"
              :key="field.name"
              v-model="form.fields[index]!"
            />
          </el-collapse>
          <el-empty v-else :image-size="60" description="Szablon nie zawiera pól do wypełnienia." />
        </el-col>
      </el-row>
    </el-form>

    <div class="editor-actions">
      <el-popconfirm
        title="Czy na pewno chcesz usunąć ten szablon?"
        confirm-button-text="Tak"
        cancel-button-text="Nie"
        @confirm="handleDelete"
      >
        <template #reference>
          <el-button type="danger" plain :loading="isDeleting">Usuń</el-button>
        </template>
      </el-popconfirm>

      <div class="editor-actions-main">
        <template v-if="isDraft">
          <el-button :loading="isSaving" @click="handleSave">Zapisz</el-button>
          <el-button type="primary" :loading="isPublishing" @click="handlePublish">
            Zapisz i opublikuj
          </el-button>
        </template>
        <el-button v-else-if="isPublished" :loading="isPublishing" @click="handleUnpublish">
          Wycofaj publikację
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.template-editor {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.editor-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.download-button {
  margin-left: auto;
}

.fields-title {
  margin-top: 0;
}

.fields-collapse {
  --el-collapse-header-bg-color: transparent;
  --el-collapse-content-bg-color: transparent;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  overflow: hidden;
}

.fields-collapse :deep(.el-collapse-item__header),
.fields-collapse :deep(.el-collapse-item__content) {
  padding-left: 16px;
  padding-right: 16px;
}

.editor-actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.editor-actions-main {
  display: flex;
  gap: 8px;
}
</style>
