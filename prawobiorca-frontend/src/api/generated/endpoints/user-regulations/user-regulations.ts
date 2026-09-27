import type {
  GetUserRegulationsParams,
  RegulationData,
  RegulationRepresentation,
  RegulationUploadTarget,
  SearchResult,
  SearchUserRegulationDocumentsParams,
} from '../../model'

import { prawobiorcaRequest } from '../../../axios'

type SecondParameter<T extends (...args: never) => unknown> = Parameters<T>[1]

/**
 * @summary Get User Regulations
 */
export const getUserRegulations = (
  params?: GetUserRegulationsParams,
  options?: SecondParameter<typeof prawobiorcaRequest<RegulationRepresentation[]>>,
) => {
  return prawobiorcaRequest<RegulationRepresentation[]>(
    { url: `/api/user/regulations`, method: 'GET', params },
    options,
  )
}
/**
 * @summary Add User Regulation
 */
export const addUserRegulation = (
  regulationData: RegulationData,
  options?: SecondParameter<typeof prawobiorcaRequest<RegulationUploadTarget>>,
) => {
  return prawobiorcaRequest<RegulationUploadTarget>(
    {
      url: `/api/user/regulations`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      data: regulationData,
    },
    options,
  )
}
/**
 * @summary Confirm User Regulation Upload
 */
export const confirmUserRegulationUpload = (
  regulationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<unknown>>,
) => {
  return prawobiorcaRequest<unknown>(
    { url: `/api/user/regulations/${regulationId}/confirm-upload`, method: 'POST' },
    options,
  )
}
/**
 * @summary Get User Regulation Download Url
 */
export const getUserRegulationDownloadUrl = (
  regulationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<string>>,
) => {
  return prawobiorcaRequest<string>(
    { url: `/api/user/regulations/${regulationId}/download-url`, method: 'GET' },
    options,
  )
}
/**
 * @summary Delete User Regulation
 */
export const deleteUserRegulation = (
  regulationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<void>>,
) => {
  return prawobiorcaRequest<void>(
    { url: `/api/user/regulations/${regulationId}`, method: 'DELETE' },
    options,
  )
}
/**
 * @summary Search User Regulation Documents
 */
export const searchUserRegulationDocuments = (
  regulationId: string,
  params: SearchUserRegulationDocumentsParams,
  options?: SecondParameter<typeof prawobiorcaRequest<SearchResult[]>>,
) => {
  return prawobiorcaRequest<SearchResult[]>(
    { url: `/api/user/regulations/${regulationId}/documents`, method: 'GET', params },
    options,
  )
}
/**
 * @summary Retry User Regulation Preparation
 */
export const retryUserRegulationPreparation = (
  regulationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<unknown>>,
) => {
  return prawobiorcaRequest<unknown>(
    { url: `/api/user/regulations/${regulationId}/preparation-retry`, method: 'POST' },
    options,
  )
}
export type GetUserRegulationsResult = NonNullable<Awaited<ReturnType<typeof getUserRegulations>>>
export type AddUserRegulationResult = NonNullable<Awaited<ReturnType<typeof addUserRegulation>>>
export type ConfirmUserRegulationUploadResult = NonNullable<
  Awaited<ReturnType<typeof confirmUserRegulationUpload>>
>
export type GetUserRegulationDownloadUrlResult = NonNullable<
  Awaited<ReturnType<typeof getUserRegulationDownloadUrl>>
>
export type DeleteUserRegulationResult = NonNullable<
  Awaited<ReturnType<typeof deleteUserRegulation>>
>
export type SearchUserRegulationDocumentsResult = NonNullable<
  Awaited<ReturnType<typeof searchUserRegulationDocuments>>
>
export type RetryUserRegulationPreparationResult = NonNullable<
  Awaited<ReturnType<typeof retryUserRegulationPreparation>>
>
