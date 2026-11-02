export type SearchPublishedApplicationTemplatesParams = {
  /**
   * @minLength 1
   */
  query: string
  aiAssisted?: boolean
  organizationId?: string | null
  suborganizationId?: string | null
}
