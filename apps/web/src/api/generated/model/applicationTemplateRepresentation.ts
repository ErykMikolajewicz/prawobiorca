import type { ApplicationTemplateFieldOutput } from './applicationTemplateFieldOutput'
import type { ApplicationTemplateStatus } from './applicationTemplateStatus'
import type { DescriptionStatus } from './descriptionStatus'

export interface ApplicationTemplateRepresentation {
  id: string
  createDate: string
  name: string
  status: ApplicationTemplateStatus
  fields: ApplicationTemplateFieldOutput[]
  instructions: string | null
  description: string | null
  descriptionStatus: DescriptionStatus
  organizationId: string | null
  suborganizationId: string | null
}
