import type { SearchResultElement } from './searchResultElement'
import type { SearchResultHighlight } from './searchResultHighlight'

export interface SearchResult {
  id: string
  /**
   * @minimum -1
   * @maximum 1
   */
  score: number
  header: string | null
  text: string
  elements: SearchResultElement[]
  highlight: SearchResultHighlight | null
}
