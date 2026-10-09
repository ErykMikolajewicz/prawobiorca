import type { ApplicationGenerationStatus } from './applicationGenerationStatus'

export interface ApplicationRepresentation {
  id: string
  caseId: string
  createDate: string
  templateName: string
  generationStatus: ApplicationGenerationStatus
  name: string | null
}
