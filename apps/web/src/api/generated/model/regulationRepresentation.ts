import type { DescriptionStatus } from './descriptionStatus'
import type { RegulationPreparationFailureReason } from './regulationPreparationFailureReason'
import type { RegulationPreparationStatus } from './regulationPreparationStatus'
import type { RegulationType } from './regulationType'

export interface RegulationRepresentation {
  id: string
  createDate: string
  /**
   * @minLength 1
   * @maxLength 255
   */
  presentationName: string
  description: string | null
  regulationType: RegulationType | null
  preparationStatus: RegulationPreparationStatus
  preparationFailureReason: RegulationPreparationFailureReason | null
  descriptionStatus: DescriptionStatus
  sectionSummariesStatus: DescriptionStatus
  organizationId: string | null
  suborganizationId: string | null
}
