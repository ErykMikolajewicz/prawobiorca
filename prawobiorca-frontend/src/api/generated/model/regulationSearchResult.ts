import type { RegulationRepresentation } from './regulationRepresentation'

export interface RegulationSearchResult {
  regulation: RegulationRepresentation
  score: number
}
