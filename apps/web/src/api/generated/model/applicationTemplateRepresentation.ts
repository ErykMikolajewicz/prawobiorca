import type { ApplicationTemplateDescriptionStatus } from './applicationTemplateDescriptionStatus'
import type { ApplicationTemplateFieldOutput } from './applicationTemplateFieldOutput'
import type { ApplicationTemplateStatus } from './applicationTemplateStatus'

export interface ApplicationTemplateRepresentation {
  id: string
  createDate: string
  name: string
  status: ApplicationTemplateStatus
  fields: ApplicationTemplateFieldOutput[]
  instructions: string | null
  description: string | null
  descriptionStatus: ApplicationTemplateDescriptionStatus
  organizationId: string | null
  suborganizationId: string | null
}
