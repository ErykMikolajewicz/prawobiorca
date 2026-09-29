import type {
  GetPublicRegulationsParams,
  RegulationData,
  RegulationDetailsData,
  RegulationRepresentation,
  RegulationUploadTarget,
  SearchRegulationDocumentsParams,
  SearchResult,
} from '../../model'

import { prawobiorcaRequest } from '../../../axios'

type SecondParameter<T extends (...args: never) => unknown> = Parameters<T>[1]

/**
 * @summary Get Public Regulations
 */
export const getPublicRegulations = (
  params?: GetPublicRegulationsParams,
  options?: SecondParameter<typeof prawobiorcaRequest<RegulationRepresentation[]>>,
) => {
  return prawobiorcaRequest<RegulationRepresentation[]>(
    { url: `/api/regulations`, method: 'GET', params },
    options,
  )
}
/**
 * @summary Add Public Regulation
 */
export const addPublicRegulation = (
  regulationData: RegulationData,
  options?: SecondParameter<typeof prawobiorcaRequest<RegulationUploadTarget>>,
) => {
  return prawobiorcaRequest<RegulationUploadTarget>(
    {
      url: `/api/regulations`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      data: regulationData,
    },
    options,
  )
}
/**
 * @summary Get Public Regulation
 */
export const getPublicRegulation = (
  regulationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<RegulationRepresentation>>,
) => {
  return prawobiorcaRequest<RegulationRepresentation>(
    { url: `/api/regulations/${regulationId}`, method: 'GET' },
    options,
  )
}
/**
 * @summary Update Public Regulation
 */
export const updatePublicRegulation = (
  regulationId: string,
  regulationDetailsData: RegulationDetailsData,
  options?: SecondParameter<typeof prawobiorcaRequest<RegulationRepresentation>>,
) => {
  return prawobiorcaRequest<RegulationRepresentation>(
    {
      url: `/api/regulations/${regulationId}`,
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      data: regulationDetailsData,
    },
    options,
  )
}
/**
 * @summary Delete Public Regulation
 */
export const deletePublicRegulation = (
  regulationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<void>>,
) => {
  return prawobiorcaRequest<void>(
    { url: `/api/regulations/${regulationId}`, method: 'DELETE' },
    options,
  )
}
/**
 * @summary Search Regulation Documents
 */
export const searchRegulationDocuments = (
  regulationId: string,
  params: SearchRegulationDocumentsParams,
  options?: SecondParameter<typeof prawobiorcaRequest<SearchResult[]>>,
) => {
  return prawobiorcaRequest<SearchResult[]>(
    { url: `/api/regulations/${regulationId}/documents`, method: 'GET', params },
    options,
  )
}
/**
 * @summary Confirm Public Regulation Upload
 */
export const confirmPublicRegulationUpload = (
  regulationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<unknown>>,
) => {
  return prawobiorcaRequest<unknown>(
    { url: `/api/regulations/${regulationId}/confirm-upload`, method: 'POST' },
    options,
  )
}
/**
 * @summary Get Public Regulation Download Url
 */
export const getPublicRegulationDownloadUrl = (
  regulationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<string>>,
) => {
  return prawobiorcaRequest<string>(
    { url: `/api/regulations/${regulationId}/download-url`, method: 'GET' },
    options,
  )
}
/**
 * @summary Retry Public Regulation Preparation
 */
export const retryPublicRegulationPreparation = (
  regulationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<unknown>>,
) => {
  return prawobiorcaRequest<unknown>(
    { url: `/api/regulations/${regulationId}/preparation-retry`, method: 'POST' },
    options,
  )
}
export type GetPublicRegulationsResult = NonNullable<
  Awaited<ReturnType<typeof getPublicRegulations>>
>
export type AddPublicRegulationResult = NonNullable<Awaited<ReturnType<typeof addPublicRegulation>>>
export type GetPublicRegulationResult = NonNullable<Awaited<ReturnType<typeof getPublicRegulation>>>
export type UpdatePublicRegulationResult = NonNullable<
  Awaited<ReturnType<typeof updatePublicRegulation>>
>
export type DeletePublicRegulationResult = NonNullable<
  Awaited<ReturnType<typeof deletePublicRegulation>>
>
export type SearchRegulationDocumentsResult = NonNullable<
  Awaited<ReturnType<typeof searchRegulationDocuments>>
>
export type ConfirmPublicRegulationUploadResult = NonNullable<
  Awaited<ReturnType<typeof confirmPublicRegulationUpload>>
>
export type GetPublicRegulationDownloadUrlResult = NonNullable<
  Awaited<ReturnType<typeof getPublicRegulationDownloadUrl>>
>
export type RetryPublicRegulationPreparationResult = NonNullable<
  Awaited<ReturnType<typeof retryPublicRegulationPreparation>>
>
