import type {
  GetRegulationsParams,
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
 * @summary Get Regulations
 */
export const getRegulations = (
  params?: GetRegulationsParams,
  options?: SecondParameter<typeof prawobiorcaRequest<RegulationRepresentation[]>>,
) => {
  return prawobiorcaRequest<RegulationRepresentation[]>(
    { url: `/api/regulations`, method: 'GET', params },
    options,
  )
}
/**
 * @summary Add Regulation
 */
export const addRegulation = (
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
 * @summary Get Regulation By Id
 */
export const getRegulationById = (
  regulationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<RegulationRepresentation>>,
) => {
  return prawobiorcaRequest<RegulationRepresentation>(
    { url: `/api/regulations/${regulationId}`, method: 'GET' },
    options,
  )
}
/**
 * @summary Update Regulation
 */
export const updateRegulation = (
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
 * @summary Delete Regulation
 */
export const deleteRegulation = (
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
 * @summary Confirm Regulation Upload
 */
export const confirmRegulationUpload = (
  regulationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<unknown>>,
) => {
  return prawobiorcaRequest<unknown>(
    { url: `/api/regulations/${regulationId}/confirm-upload`, method: 'POST' },
    options,
  )
}
/**
 * @summary Get Regulation Download Url By Id
 */
export const getRegulationDownloadUrlById = (
  regulationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<string>>,
) => {
  return prawobiorcaRequest<string>(
    { url: `/api/regulations/${regulationId}/download-url`, method: 'GET' },
    options,
  )
}
/**
 * @summary Retry Regulation Preparation
 */
export const retryRegulationPreparation = (
  regulationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<unknown>>,
) => {
  return prawobiorcaRequest<unknown>(
    { url: `/api/regulations/${regulationId}/preparation-retry`, method: 'POST' },
    options,
  )
}
export type GetRegulationsResult = NonNullable<Awaited<ReturnType<typeof getRegulations>>>
export type AddRegulationResult = NonNullable<Awaited<ReturnType<typeof addRegulation>>>
export type GetRegulationByIdResult = NonNullable<Awaited<ReturnType<typeof getRegulationById>>>
export type UpdateRegulationResult = NonNullable<Awaited<ReturnType<typeof updateRegulation>>>
export type DeleteRegulationResult = NonNullable<Awaited<ReturnType<typeof deleteRegulation>>>
export type SearchRegulationDocumentsResult = NonNullable<
  Awaited<ReturnType<typeof searchRegulationDocuments>>
>
export type ConfirmRegulationUploadResult = NonNullable<
  Awaited<ReturnType<typeof confirmRegulationUpload>>
>
export type GetRegulationDownloadUrlByIdResult = NonNullable<
  Awaited<ReturnType<typeof getRegulationDownloadUrlById>>
>
export type RetryRegulationPreparationResult = NonNullable<
  Awaited<ReturnType<typeof retryRegulationPreparation>>
>
