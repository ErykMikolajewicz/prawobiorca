import type { SearchResultElement } from './searchResultElement'

export interface SectionRepresentation {
  id: string
  header: string | null
  text: string
  elements: SearchResultElement[]
  summary_label: string | null
  summary: string | null
}
