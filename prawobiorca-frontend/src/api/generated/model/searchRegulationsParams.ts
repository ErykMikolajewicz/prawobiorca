import type { RegulationScope } from './regulationScope'
import type { RegulationType } from './regulationType'

export type SearchRegulationsParams = {
  /**
   * @minLength 1
   */
  query: string
  /**
   * @minimum -1
   * @maximum 1
   */
  threshold: number
  scope?: RegulationScope
  documentType?: RegulationType | null
  organizationId?: string | null
  suborganizationId?: string | null
}
