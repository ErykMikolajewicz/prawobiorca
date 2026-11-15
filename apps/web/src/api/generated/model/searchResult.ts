import type { SearchResultElement } from './searchResultElement'
import type { SearchResultHighlight } from './searchResultHighlight'

export interface SearchResult {
  id: string
  header: string | null
  text: string
  elements: SearchResultElement[]
  summary_label: string | null
  summary: string | null
  /**
   * @minimum -1
   * @maximum 1
   */
  score: number
  highlight: SearchResultHighlight | null
}
