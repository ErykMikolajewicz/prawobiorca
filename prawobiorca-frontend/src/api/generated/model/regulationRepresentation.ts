import type { RegulationPreparationStatus } from './regulationPreparationStatus'
import type { RegulationType } from './regulationType'

export interface RegulationRepresentation {
  id: string
  /**
   * @minLength 1
   * @maxLength 255
   */
  presentationName: string
  regulationType: RegulationType | null
  preparationStatus: RegulationPreparationStatus
}
