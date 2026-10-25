export type RegulationDescriptionStatus =
  (typeof RegulationDescriptionStatus)[keyof typeof RegulationDescriptionStatus]

export const RegulationDescriptionStatus = {
  NOT_REQUESTED: 'NOT_REQUESTED',
  IN_PROGRESS: 'IN_PROGRESS',
  GENERATED: 'GENERATED',
  FAILED: 'FAILED',
} as const
