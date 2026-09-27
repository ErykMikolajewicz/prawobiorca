export type RegulationPreparationStatus =
  (typeof RegulationPreparationStatus)[keyof typeof RegulationPreparationStatus]

export const RegulationPreparationStatus = {
  NOT_STARTED: 'NOT_STARTED',
  IN_PROGRESS: 'IN_PROGRESS',
  PREPARED: 'PREPARED',
  FAILED: 'FAILED',
} as const
