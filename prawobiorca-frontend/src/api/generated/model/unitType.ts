export type UnitType = (typeof UnitType)[keyof typeof UnitType]

export const UnitType = {
  ARTICLE: 'ARTICLE',
  PARAGRAPH: 'PARAGRAPH',
  UNNUMBERED: 'UNNUMBERED',
} as const
