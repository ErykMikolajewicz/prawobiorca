import type { SearchResultElement } from './searchResultElement'
import type { SearchResultHighlight } from './searchResultHighlight'
import type { UnitType } from './unitType'

export interface SearchResult {
  id: string
  /**
   * @minimum -1
   * @maximum 1
   */
  score: number
  header: string | null
  text: string
  unit_type: UnitType | null
  unit_number: string | null
  unit_path: string[] | null
  elements: SearchResultElement[] | null
  highlight: SearchResultHighlight | null
}
