<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { FormInstance, FormItemRule } from 'element-plus'

import { DATE_VALUE_FORMAT } from '@/domain/applicationTemplates'
import type { NewApplication, PublishedApplicationTemplate } from '@/api/generated/model'

type Props = {
  templates: Array<PublishedApplicationTemplate>
  scores?: Record<string, number> | null
  searching?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'generate-pdf', newApplication: NewApplication): void
  (e: 'search', query: string): void
}>()

const formRef = ref<FormInstance>()

const form = reactive({
  templateId: '',
  description: '',
  fieldValues: {} as Record<string, string>,
})

const selectedTemplate = computed(() =>
  props.templates.find((template) => template.id === form.templateId),
)

const visibleTemplates = computed(() => {
  const scores = props.scores
  if (!scores) {
    return props.templates
  }
  const scoredTemplates = props.templates.filter((template) => template.id in scores)
  scoredTemplates.sort((a, b) => scores[b.id]! - scores[a.id]!)
  return scoredTemplates
})

function handleSearch(query: string) {
  emit('search', query.trim())
}

const rules = computed(() => {
  const fieldRules: Record<string, Array<FormItemRule>> = {
    templateId: [{ required: true, message: 'Wybierz szablon wniosku.', trigger: 'change' }],
    description: [{ required: true, message: 'Opisz swoją sytuację.', trigger: 'blur' }],
  }
  for (const field of selectedTemplate.value?.fields ?? []) {
    const itemRules: Array<FormItemRule> = [
      { required: field.required, message: 'To pole jest wymagane.', trigger: ['blur', 'change'] },
    ]
    if (field.pattern) {
      itemRules.push({
        pattern: new RegExp(`^(?:${field.pattern})$`),
        message: 'Nieprawidłowy format.',
        trigger: 'blur',
      })
    }
    fieldRules[`fieldValues.${field.name}`] = itemRules
  }
  return fieldRules
})

function handleTemplateChange() {
  form.fieldValues = Object.fromEntries(
    (selectedTemplate.value?.fields ?? []).map((field) => [field.name, field.defaultValue ?? '']),
  )
  formRef.value?.clearValidate()
}

watch(
  () => props.templates,
  () => {
    if (form.templateId && !selectedTemplate.value) {
      form.templateId = ''
      handleTemplateChange()
    }
  },
)

async function handleSubmit() {
  if (!(await formRef.value?.validate().catch(() => false))) {
    return
  }
  emit('generate-pdf', {
    templateId: form.templateId,
    description: form.description,
    fieldValues: { ...form.fieldValues },
  })
}
</script>

<template>
  <el-form
    ref="formRef"
    :model="form"
    :rules="rules"
    label-position="top"
    @submit.prevent="handleSubmit"
  >
    <el-form-item label="Rodzaj wniosku:" prop="templateId">
      <el-select
        v-model="form.templateId"
        filterable
        remote
        remote-show-suffix
        :remote-method="handleSearch"
        :debounce="500"
        :loading="searching"
        placeholder="Wpisz, czego dotyczy wniosek, np. przedłużenie terminu oddania pracy dyplomowej"
        loading-text="Wyszukiwanie szablonów..."
        :no-data-text="
          scores ? 'Nie znaleziono pasujących szablonów.' : 'Brak dostępnych szablonów'
        "
        @change="handleTemplateChange"
      >
        <el-option
          v-for="template in visibleTemplates"
          :key="template.id"
          :label="template.name"
          :value="template.id"
        >
          <el-tooltip
            :content="template.description ?? ''"
            :disabled="!template.description"
            placement="right"
            popper-class="template-description-tooltip"
          >
            <span class="template-option">
              <span class="template-option-name">{{ template.name }}</span>
              <span v-if="scores" class="template-option-score">
                {{ scores[template.id]?.toFixed(3) }}
              </span>
            </span>
          </el-tooltip>
        </el-option>
      </el-select>
    </el-form-item>
    <el-form-item
      v-for="field in selectedTemplate?.fields ?? []"
      :key="field.name"
      :label="`${field.label}:`"
      :prop="`fieldValues.${field.name}`"
    >
      <el-select
        v-if="field.fieldType === 'SELECT'"
        v-model="form.fieldValues[field.name]"
        :clearable="!field.required"
      >
        <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
      </el-select>
      <el-date-picker
        v-else-if="field.fieldType === 'DATE'"
        v-model="form.fieldValues[field.name]"
        type="date"
        :format="DATE_VALUE_FORMAT"
        :value-format="DATE_VALUE_FORMAT"
      />
      <el-input
        v-else
        v-model="form.fieldValues[field.name]"
        :type="field.fieldType === 'NUMBER' ? 'number' : 'text'"
      />
    </el-form-item>
    <el-form-item label="Opisz swoją sytuację lub cel pisma:" prop="description">
      <el-input
        v-model="form.description"
        type="textarea"
        :rows="10"
        placeholder="np. Proszę o zapomogę finansową ze względu na trudną sytuację, w której znalazłem się po śmierci rodzica..."
      />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" native-type="submit"> Generuj Wniosek (DOCX) </el-button>
    </el-form-item>
  </el-form>
</template>

<style scoped>
.template-option {
  display: flex;
  justify-content: space-between;
  gap: var(--app-space-md);
}

.template-option-name {
  overflow: hidden;
  text-overflow: ellipsis;
}

.template-option-score {
  flex-shrink: 0;
  color: var(--el-text-color-secondary);
  font-size: 0.8rem;
}
</style>

<style>
.template-description-tooltip {
  max-width: 400px;
  line-height: 1.4;
}
</style>
