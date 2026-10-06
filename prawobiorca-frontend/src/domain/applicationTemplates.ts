import type {
  ApplicationFieldType,
  ApplicationTemplateField,
  ApplicationTemplateStatus,
} from '@/api/generated/model'

export type TemplateStatusOption = {
  label: string
  tagType: 'info' | 'success' | 'danger'
}

export type EditableTemplateField = Required<ApplicationTemplateField>

export const DATE_VALUE_FORMAT = 'DD.MM.YYYY'

export const fieldTypeOptions: Array<{ label: string; value: ApplicationFieldType }> = [
  { label: 'Tekst', value: 'TEXT' },
  { label: 'Liczba', value: 'NUMBER' },
  { label: 'Lista wyboru', value: 'SELECT' },
  { label: 'Data', value: 'DATE' },
]

export const templateStatusOptions: Record<ApplicationTemplateStatus, TemplateStatusOption> = {
  NOT_UPLOADED: { label: 'Niewczytany', tagType: 'danger' },
  DRAFT: { label: 'Szkic', tagType: 'info' },
  PUBLISHED: { label: 'Opublikowany', tagType: 'success' },
}

export function toEditableField(field: ApplicationTemplateField): EditableTemplateField {
  return {
    name: field.name,
    label: field.label,
    fieldType: field.fieldType ?? 'TEXT',
    required: field.required ?? true,
    passToAi: field.passToAi ?? true,
    defaultValue: field.defaultValue ?? null,
    pattern: field.pattern ?? null,
    options: [...(field.options ?? [])],
  }
}
