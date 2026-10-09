<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { MdEditor, type ToolbarNames } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { showApiError } from '@/utils/error'
import { useDarkMode } from '@/composables/useDarkMode'
import { downloadApplicationTemplate } from '@/api/applicationTemplates'
import ApplicationTemplateStatusBadge from '@/components/atoms/ApplicationTemplateStatusBadge.vue'
import ApplicationTemplateFieldEditor from '@/components/molecules/ApplicationTemplateFieldEditor.vue'
import ApplicationTemplatePreviewDialog from '@/components/molecules/ApplicationTemplatePreviewDialog.vue'
import {
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
}>()

const form = reactive({
  name: '',
  instructions: '',
  fields: [] as Array<EditableTemplateField>,
})

const instructionsToolbars: Array<ToolbarNames> = [
  'bold',
  'italic',
  'title',
  '-',
  'unorderedList',
  'orderedList',
  'quote',
  '-',
  'revoke',
  'next',
  '=',
  'preview',
  'pageFullscreen',
]

const { isDark } = useDarkMode()

const isSaving = ref(false)
const isPublishing = ref(false)
const isDownloading = ref(false)
const isPreviewVisible = ref(false)

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
</script>

<template>
  <div class="template-editor">
    <div class="editor-header">
      <div v-if="isDraft" class="section-title name-title">
        <el-input v-model="form.name" class="name-input" placeholder="Nazwa szablonu" />
      </div>
      <h2 v-else class="section-title">{{ template.name }}</h2>
      <ApplicationTemplateStatusBadge :status="template.status" />
    </div>

    <div class="editor-actions">
      <el-button v-if="!isNotUploaded" :loading="isDownloading" @click="handleDownload">
        Pobierz szablon
      </el-button>
      <el-button v-if="!isNotUploaded" @click="isPreviewVisible = true">Pokaż podgląd</el-button>
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
          <el-form-item label="Instrukcje dla AI:">
            <MdEditor
              v-model="form.instructions"
              class="instructions-input"
              language="en-US"
              :theme="isDark ? 'dark' : 'light'"
              :toolbars="instructionsToolbars"
              :read-only="!isDraft"
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

    <ApplicationTemplatePreviewDialog v-model="isPreviewVisible" :template-id="template.id" />
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

.name-title {
  flex: 1;
  min-width: 0;
}

.name-input {
  font-size: inherit;
  font-weight: inherit;
}

.name-input :deep(.el-input__wrapper) {
  padding-left: 4px;
  background-color: transparent;
  box-shadow: none;
}

.name-input :deep(.el-input__wrapper:hover),
.name-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--el-input-hover-border-color) inset;
}

.name-input :deep(.el-input__inner) {
  height: auto;
  font-size: inherit;
  font-weight: inherit;
  color: inherit;
}

.instructions-input {
  height: 50vh;
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
  gap: 8px;
}
</style>
