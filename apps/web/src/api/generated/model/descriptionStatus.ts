export type DescriptionStatus = (typeof DescriptionStatus)[keyof typeof DescriptionStatus]

export const DescriptionStatus = {
  NOT_REQUESTED: 'NOT_REQUESTED',
  IN_PROGRESS: 'IN_PROGRESS',
  GENERATED: 'GENERATED',
  FAILED: 'FAILED',
} as const
