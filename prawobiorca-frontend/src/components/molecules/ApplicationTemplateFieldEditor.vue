<script setup lang="ts">
import {
  DATE_VALUE_FORMAT,
  fieldTypeOptions,
  type EditableTemplateField,
} from '@/domain/applicationTemplates'

const field = defineModel<EditableTemplateField>({ required: true })

function handleFieldTypeChange() {
  if (field.value.fieldType !== 'TEXT') {
    field.value.pattern = null
  }
  if (field.value.fieldType !== 'SELECT') {
    field.value.options = []
  }
  field.value.defaultValue = null
}
</script>

<template>
  <el-collapse-item :name="field.name">
    <template #title>
      <code class="field-name">{{ field.name }}</code>
    </template>

    <el-row :gutter="16">
      <el-col :span="12" :xs="24">
        <el-form-item label="Etykieta:">
          <el-input v-model="field.label" />
        </el-form-item>
      </el-col>

      <el-col :span="12" :xs="24">
        <el-form-item label="Typ:">
          <el-select v-model="field.fieldType" @change="handleFieldTypeChange">
            <el-option
              v-for="option in fieldTypeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
      </el-col>

      <el-col v-if="field.fieldType === 'TEXT'" :span="12" :xs="24">
        <el-form-item label="Regex walidacji (opcjonalnie):">
          <el-input v-model="field.pattern" clearable placeholder="np. \d{6}" />
        </el-form-item>
      </el-col>

      <el-col v-if="field.fieldType === 'SELECT'" :span="12" :xs="24">
        <el-form-item label="Opcje listy:">
          <el-select
            v-model="field.options"
            multiple
            filterable
            allow-create
            default-first-option
            :reserve-keyword="false"
            placeholder="Wpisz opcję i naciśnij Enter"
          />
        </el-form-item>
      </el-col>

      <el-col :span="12" :xs="24">
        <el-form-item label="Wartość domyślna (opcjonalnie):">
          <el-select
            v-if="field.fieldType === 'SELECT'"
            v-model="field.defaultValue"
            clearable
            placeholder="Brak"
          >
            <el-option
              v-for="option in field.options"
              :key="option"
              :label="option"
              :value="option"
            />
          </el-select>
          <el-date-picker
            v-else-if="field.fieldType === 'DATE'"
            v-model="field.defaultValue"
            type="date"
            :format="DATE_VALUE_FORMAT"
            :value-format="DATE_VALUE_FORMAT"
            placeholder="Brak"
          />
          <el-input v-else v-model="field.defaultValue" clearable placeholder="Brak" />
        </el-form-item>
      </el-col>
    </el-row>

    <div class="field-flags">
      <el-checkbox v-model="field.required">Wymagane</el-checkbox>
      <el-checkbox v-model="field.passToAi">Przekaż do AI</el-checkbox>
    </div>
  </el-collapse-item>
</template>

<style scoped>
.field-name {
  color: var(--el-color-primary);
  font-weight: 600;
}

.field-flags {
  display: flex;
  gap: 1.5rem;
}
</style>
