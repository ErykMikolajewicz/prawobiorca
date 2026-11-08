export type ApplicationFieldType = (typeof ApplicationFieldType)[keyof typeof ApplicationFieldType]

export const ApplicationFieldType = {
  TEXT: 'TEXT',
  NUMBER: 'NUMBER',
  SELECT: 'SELECT',
  DATE: 'DATE',
} as const
