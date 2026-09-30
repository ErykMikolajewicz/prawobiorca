import type { components } from '@/types/api/schema.ts'

export type regulationType = components['schemas']['RegulationType']

export type regulationPreparationStatus = components['schemas']['RegulationPreparationStatus']

export type regulationRepresentation = components['schemas']['RegulationRepresentation']

export type regulationData = components['schemas']['RegulationData']

export type regulationUploadTarget = components['schemas']['RegulationUploadTarget']

export type regulationUploadResult = {
  id: string
  preparationStatus: regulationPreparationStatus
}
