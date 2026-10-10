import type { ApplicationTemplateField } from './applicationTemplateField'

export interface ApplicationTemplateDetailsData {
  /**
   * @minLength 1
   * @maxLength 255
   */
  name: string
  instructions?: string | null
  fields: ApplicationTemplateField[]
  organizationId?: string | null
  suborganizationId?: string | null
}
