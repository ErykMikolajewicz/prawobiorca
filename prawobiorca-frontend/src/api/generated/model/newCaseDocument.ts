export interface NewCaseDocument {
  /** @minLength 1 */
  presentationName: string
  /** @minLength 1 */
  content: string
  header?: string | null
}
