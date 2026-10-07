<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import type { FormInstance, FormItemRule } from 'element-plus'

import { DATE_VALUE_FORMAT } from '@/domain/applicationTemplates'
import type { NewApplication, PublishedApplicationTemplate } from '@/api/generated/model'

type Props = {
  templates: Array<PublishedApplicationTemplate>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'generate-pdf', newApplication: NewApplication): void
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
        placeholder="Wybierz szablon"
        no-data-text="Brak dostępnych szablonów"
        @change="handleTemplateChange"
      >
        <el-option
          v-for="template in templates"
          :key="template.id"
          :label="template.name"
          :value="template.id"
        />
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
