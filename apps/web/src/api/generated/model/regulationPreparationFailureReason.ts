export type RegulationPreparationFailureReason =
  (typeof RegulationPreparationFailureReason)[keyof typeof RegulationPreparationFailureReason]

export const RegulationPreparationFailureReason = {
  INCOMPLETE_DOCUMENT: 'INCOMPLETE_DOCUMENT',
  UNREADABLE_DOCUMENT: 'UNREADABLE_DOCUMENT',
  PROCESSING_ERROR: 'PROCESSING_ERROR',
} as const
