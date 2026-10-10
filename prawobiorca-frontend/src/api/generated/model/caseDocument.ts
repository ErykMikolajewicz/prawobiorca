import type { SearchResultElement } from './searchResultElement'
import type { SearchResultHighlight } from './searchResultHighlight'

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
  header: string | null
  elements: SearchResultElement[]
  highlight: SearchResultHighlight | null
}
