import type { components, operations } from '@/types/api/schema.ts'

export type searchResultElement = components['schemas']['SearchResultElement']

export type searchResultHighlight = components['schemas']['SearchResultHighlight']

export type searchResult = components['schemas']['SearchResult']

export type searchOrder = components['schemas']['SearchOrder']

export type searchParams =
  operations['search_regulation_documents_api_regulations__regulationId__documents_get']['parameters']['query']
