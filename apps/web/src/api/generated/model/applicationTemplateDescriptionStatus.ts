export type ApplicationTemplateDescriptionStatus =
  (typeof ApplicationTemplateDescriptionStatus)[keyof typeof ApplicationTemplateDescriptionStatus]

export const ApplicationTemplateDescriptionStatus = {
  NOT_REQUESTED: 'NOT_REQUESTED',
  IN_PROGRESS: 'IN_PROGRESS',
  GENERATED: 'GENERATED',
  FAILED: 'FAILED',
} as const
