export type ApplicationTemplateStatus =
  (typeof ApplicationTemplateStatus)[keyof typeof ApplicationTemplateStatus]

export const ApplicationTemplateStatus = {
  NOT_UPLOADED: 'NOT_UPLOADED',
  DRAFT: 'DRAFT',
  PUBLISHED: 'PUBLISHED',
} as const
