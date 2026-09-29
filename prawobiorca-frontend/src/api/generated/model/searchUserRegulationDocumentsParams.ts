import type { SearchOrder } from './searchOrder'

export type SearchUserRegulationDocumentsParams = {
  /**
   * @minimum -1
   * @maximum 1
   */
  threshold: number
  limit?: number | null
  query: string
  order_by?: SearchOrder
}
