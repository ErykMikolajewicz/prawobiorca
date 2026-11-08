export type SearchOrder = (typeof SearchOrder)[keyof typeof SearchOrder]

export const SearchOrder = {
  document: 'document',
  score: 'score',
} as const
