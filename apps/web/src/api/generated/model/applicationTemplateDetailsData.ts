import type { ApplicationTemplateFieldInput } from './applicationTemplateFieldInput'

export interface ApplicationTemplateDetailsData {
  /**
   * @minLength 1
   * @maxLength 255
   */
  name: string
  instructions?: string | null
  fields: ApplicationTemplateFieldInput[]
  description?: string | null
  organizationId?: string | null
  suborganizationId?: string | null
}
