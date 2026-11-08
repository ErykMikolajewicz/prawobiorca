export type RegulationScope = (typeof RegulationScope)[keyof typeof RegulationScope]

export const RegulationScope = {
  PUBLIC: 'PUBLIC',
  PRIVATE: 'PRIVATE',
} as const
