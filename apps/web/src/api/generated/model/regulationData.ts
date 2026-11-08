import type { RegulationScope } from './regulationScope'
import type { RegulationType } from './regulationType'

export interface RegulationData {
  scope: RegulationScope
  /**
   * @minLength 1
   * @maxLength 255
   */
  name: string
  regulationType?: RegulationType | null
  organizationId?: string | null
  suborganizationId?: string | null
  generateDescription?: boolean
}
