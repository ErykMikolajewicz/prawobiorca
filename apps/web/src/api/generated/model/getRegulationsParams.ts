import type { RegulationScope } from './regulationScope'
import type { RegulationType } from './regulationType'

export type GetRegulationsParams = {
  scope?: RegulationScope
  documentType?: RegulationType | null
  organizationId?: string | null
  suborganizationId?: string | null
}
