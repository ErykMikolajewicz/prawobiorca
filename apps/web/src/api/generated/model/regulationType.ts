export type RegulationType = (typeof RegulationType)[keyof typeof RegulationType]

export const RegulationType = {
  ACT: 'ACT',
  DECREE: 'DECREE',
  STATUTE: 'STATUTE',
} as const
