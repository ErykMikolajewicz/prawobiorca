import type { RegulationType } from './regulationType'

export interface RegulationData {
  /**
   * @minLength 1
   * @maxLength 255
   */
  name: string
  regulationType?: RegulationType | null
}
