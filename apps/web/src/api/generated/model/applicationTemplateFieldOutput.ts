import type { ApplicationFieldType } from './applicationFieldType'

export interface ApplicationTemplateFieldOutput {
  name: string
  label: string
  fieldType: ApplicationFieldType
  required: boolean
  passToAi: boolean
  defaultValue: string | null
  pattern: string | null
  options: string[]
}
