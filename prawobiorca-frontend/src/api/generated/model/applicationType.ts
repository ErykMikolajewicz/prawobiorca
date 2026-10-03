export type ApplicationType = (typeof ApplicationType)[keyof typeof ApplicationType]

export const ApplicationType = {
  OTHER: 'OTHER',
  DIPLOMA_DEADLINE_EXTENSION: 'DIPLOMA_DEADLINE_EXTENSION',
} as const
