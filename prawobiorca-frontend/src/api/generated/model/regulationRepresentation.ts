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
}
