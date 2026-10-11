<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { MdEditor, type ToolbarNames } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { useDarkMode } from '@/composables/useDarkMode'
import { useApplicationTemplateEditor } from '@/composables/useApplicationTemplateEditor'
import ApplicationTemplateStatusBadge from '@/components/atoms/ApplicationTemplateStatusBadge.vue'
import ApplicationTemplateFieldEditor from '@/components/molecules/ApplicationTemplateFieldEditor.vue'
import OrganizationScopeSelect from '@/components/molecules/OrganizationScopeSelect.vue'
import ApplicationTemplatePreviewDialog from '@/components/molecules/ApplicationTemplatePreviewDialog.vue'
import type { ApplicationTemplateRepresentation } from '@/api/generated/model'

type Props = {
  template: ApplicationTemplateRepresentation
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'updated', template: ApplicationTemplateRepresentation): void
}>()

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

const {
  form,
  isSaving,
  isPublishing,
  isDownloading,
  resetForm,
  save,
  publish,
  unpublish,
  download,
} = useApplicationTemplateEditor((template) => emit('updated', template))

const isPreviewVisible = ref(false)

const isDraft = computed(() => props.template.status === 'DRAFT')
const isPublished = computed(() => props.template.status === 'PUBLISHED')
const isNotUploaded = computed(() => props.template.status === 'NOT_UPLOADED')

watch(() => props.template, resetForm, { immediate: true })
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
      <el-button v-if="!isNotUploaded" :loading="isDownloading" @click="download(template.id)">
        Pobierz szablon
      </el-button>
      <el-button v-if="!isNotUploaded" @click="isPreviewVisible = true">Pokaż podgląd</el-button>
      <template v-if="isDraft">
        <el-button :loading="isSaving" @click="save(template.id)">Zapisz</el-button>
        <el-button type="primary" :loading="isPublishing" @click="publish(template.id)">
          Zapisz i opublikuj
        </el-button>
      </template>
      <el-button v-else-if="isPublished" :loading="isPublishing" @click="unpublish(template.id)">
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
      @submit.prevent="save(template.id)"
    >
      <OrganizationScopeSelect
        v-model:organization-id="form.organizationId"
        v-model:suborganization-id="form.suborganizationId"
        inline
      />

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
          <el-collapse v-if="form.fields.length" class="app-collapse">
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
  gap: var(--app-space-lg);
}

.editor-header {
  display: flex;
  align-items: center;
  gap: var(--app-space-md);
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
  padding-left: var(--app-space-xs);
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

.editor-actions {
  display: flex;
  gap: var(--app-space-sm);
}
</style>
