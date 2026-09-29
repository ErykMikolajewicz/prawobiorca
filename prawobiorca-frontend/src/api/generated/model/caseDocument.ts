export interface CaseDocument {
  id: string
  caseId: string
  /**
   * @minLength 1
   * @maxLength 255
   */
  presentationName: string
  /** @minLength 1 */
  content: string
}
