export interface RegulationDetailsData {
  /**
   * @minLength 1
   * @maxLength 255
   */
  name: string
  description?: string | null
}
