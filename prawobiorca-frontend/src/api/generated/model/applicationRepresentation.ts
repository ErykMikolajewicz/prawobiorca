import type { ApplicationType } from './applicationType'

export interface ApplicationRepresentation {
  id: string
  caseId: string
  createDate: string
  applicationType: ApplicationType
}
