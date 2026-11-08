export type ApplicationGenerationStatus =
  (typeof ApplicationGenerationStatus)[keyof typeof ApplicationGenerationStatus]

export const ApplicationGenerationStatus = {
  IN_PROGRESS: 'IN_PROGRESS',
  GENERATED: 'GENERATED',
  FAILED: 'FAILED',
} as const
