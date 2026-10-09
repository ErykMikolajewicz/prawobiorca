import type { ApplicationTemplateField } from './applicationTemplateField'
import type { ApplicationTemplateStatus } from './applicationTemplateStatus'

export interface ApplicationTemplateRepresentation {
  id: string
  createDate: string
  name: string
  status: ApplicationTemplateStatus
  fields: ApplicationTemplateField[]
  instructions: string | null
}
