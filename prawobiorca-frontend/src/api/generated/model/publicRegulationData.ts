import type { RegulationType } from './regulationType'

export interface PublicRegulationData {
  /**
   * @minLength 1
   * @maxLength 255
   */
  name: string
  regulationType?: RegulationType | null
  organizationId?: string | null
  suborganizationId?: string | null
}
