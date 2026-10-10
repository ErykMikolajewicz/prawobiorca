import type { SearchResultElement } from './searchResultElement'
import type { SearchResultHighlight } from './searchResultHighlight'

export interface NewCaseDocument {
  /** @minLength 1 */
  presentationName: string
  /** @minLength 1 */
  content: string
  header?: string | null
  elements?: SearchResultElement[]
  highlight?: SearchResultHighlight | null
}
