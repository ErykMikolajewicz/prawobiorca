import type { ApplicationFieldType } from './applicationFieldType'

export interface PublishedApplicationField {
  name: string
  label: string
  fieldType: ApplicationFieldType
  required: boolean
  defaultValue: string | null
  pattern: string | null
  options: string[]
}
