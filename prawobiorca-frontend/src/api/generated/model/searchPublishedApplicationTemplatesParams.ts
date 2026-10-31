export type SearchPublishedApplicationTemplatesParams = {
  /**
   * @minLength 1
   */
  query: string
  /**
   * @minimum -1
   * @maximum 1
   */
  threshold: number
  organizationId?: string | null
  suborganizationId?: string | null
}
