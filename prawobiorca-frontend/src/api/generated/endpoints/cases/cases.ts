import type {
  ApplicationRepresentation,
  BodyAddCase,
  CaseData,
  CaseDocument,
  NewApplication,
  NewCaseDocument,
} from '../../model'

import { prawobiorcaRequest } from '../../../axios'

type SecondParameter<T extends (...args: never) => unknown> = Parameters<T>[1]

/**
 * @summary Get Cases List
 */
export const getCasesList = (options?: SecondParameter<typeof prawobiorcaRequest<CaseData[]>>) => {
  return prawobiorcaRequest<CaseData[]>({ url: `/api/user/cases`, method: 'GET' }, options)
}
/**
 * @summary Add Case
 */
export const addCase = (
  bodyAddCase: BodyAddCase,
  options?: SecondParameter<typeof prawobiorcaRequest<string>>,
) => {
  const formUrlEncoded = new URLSearchParams()
  formUrlEncoded.append(`caseName`, bodyAddCase.caseName)

  return prawobiorcaRequest<string>(
    {
      url: `/api/user/cases`,
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      data: formUrlEncoded,
    },
    options,
  )
}
/**
 * @summary Delete User Case
 */
export const deleteUserCase = (
  caseId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<void>>,
) => {
  return prawobiorcaRequest<void>({ url: `/api/user/cases/${caseId}`, method: 'DELETE' }, options)
}
/**
 * @summary Add Case Document
 */
export const addCaseDocument = (
  caseId: string,
  newCaseDocument: NewCaseDocument,
  options?: SecondParameter<typeof prawobiorcaRequest<unknown>>,
) => {
  return prawobiorcaRequest<unknown>(
    {
      url: `/api/user/cases/${caseId}/documents`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      data: newCaseDocument,
    },
    options,
  )
}
/**
 * @summary Get Case Documents
 */
export const getCaseDocuments = (
  caseId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<CaseDocument[]>>,
) => {
  return prawobiorcaRequest<CaseDocument[]>(
    { url: `/api/user/cases/${caseId}/documents`, method: 'GET' },
    options,
  )
}
/**
 * @summary Delete Case Document
 */
export const deleteCaseDocument = (
  documentId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<void>>,
) => {
  return prawobiorcaRequest<void>(
    { url: `/api/user/cases/documents/${documentId}`, method: 'DELETE' },
    options,
  )
}
/**
 * @summary Generate Application
 */
export const generateApplication = (
  caseId: string,
  newApplication: NewApplication,
  options?: SecondParameter<typeof prawobiorcaRequest<string>>,
) => {
  return prawobiorcaRequest<string>(
    {
      url: `/api/user/cases/${caseId}/application`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      data: newApplication,
    },
    options,
  )
}
/**
 * @summary Get Case Applications
 */
export const getCaseApplications = (
  caseId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<ApplicationRepresentation[]>>,
) => {
  return prawobiorcaRequest<ApplicationRepresentation[]>(
    { url: `/api/user/cases/${caseId}/applications`, method: 'GET' },
    options,
  )
}
/**
 * @summary Get Case Application Download Url
 */
export const getCaseApplicationDownloadUrl = (
  applicationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<string>>,
) => {
  return prawobiorcaRequest<string>(
    { url: `/api/user/cases/applications/${applicationId}/download-url`, method: 'GET' },
    options,
  )
}
/**
 * @summary Delete Application
 */
export const deleteApplication = (
  applicationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<void>>,
) => {
  return prawobiorcaRequest<void>(
    { url: `/api/user/cases/applications/${applicationId}`, method: 'DELETE' },
    options,
  )
}
export type GetCasesListResult = NonNullable<Awaited<ReturnType<typeof getCasesList>>>
export type AddCaseResult = NonNullable<Awaited<ReturnType<typeof addCase>>>
export type DeleteUserCaseResult = NonNullable<Awaited<ReturnType<typeof deleteUserCase>>>
export type AddCaseDocumentResult = NonNullable<Awaited<ReturnType<typeof addCaseDocument>>>
export type GetCaseDocumentsResult = NonNullable<Awaited<ReturnType<typeof getCaseDocuments>>>
export type DeleteCaseDocumentResult = NonNullable<Awaited<ReturnType<typeof deleteCaseDocument>>>
export type GenerateApplicationResult = NonNullable<Awaited<ReturnType<typeof generateApplication>>>
export type GetCaseApplicationsResult = NonNullable<Awaited<ReturnType<typeof getCaseApplications>>>
export type GetCaseApplicationDownloadUrlResult = NonNullable<
  Awaited<ReturnType<typeof getCaseApplicationDownloadUrl>>
>
export type DeleteApplicationResult = NonNullable<Awaited<ReturnType<typeof deleteApplication>>>
