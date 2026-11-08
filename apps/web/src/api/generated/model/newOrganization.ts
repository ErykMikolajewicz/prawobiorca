export interface NewOrganization {
  /**
   * @minLength 1
   * @maxLength 255
   */
  name: string
  /**
   * @minLength 1
   * @maxLength 32
   */
  shortName: string
}
