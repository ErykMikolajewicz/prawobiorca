import type {
  ApplicationTemplateData,
  ApplicationTemplateDetailsData,
  ApplicationTemplateRepresentation,
  ApplicationTemplateUploadTarget,
  PublishedApplicationTemplate,
} from '../../model'

import { prawobiorcaRequest } from '../../../axios'

type SecondParameter<T extends (...args: never) => unknown> = Parameters<T>[1]

/**
 * @summary Get Published Application Templates
 */
export const getPublishedApplicationTemplates = (
  options?: SecondParameter<typeof prawobiorcaRequest<PublishedApplicationTemplate[]>>,
) => {
  return prawobiorcaRequest<PublishedApplicationTemplate[]>(
    { url: `/api/application-templates`, method: 'GET' },
    options,
  )
}
/**
 * @summary Get Application Templates
 */
export const getApplicationTemplates = (
  options?: SecondParameter<typeof prawobiorcaRequest<ApplicationTemplateRepresentation[]>>,
) => {
  return prawobiorcaRequest<ApplicationTemplateRepresentation[]>(
    { url: `/api/admin/application-templates`, method: 'GET' },
    options,
  )
}
/**
 * @summary Add Application Template
 */
export const addApplicationTemplate = (
  applicationTemplateData: ApplicationTemplateData,
  options?: SecondParameter<typeof prawobiorcaRequest<ApplicationTemplateUploadTarget>>,
) => {
  return prawobiorcaRequest<ApplicationTemplateUploadTarget>(
    {
      url: `/api/admin/application-templates`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      data: applicationTemplateData,
    },
    options,
  )
}
/**
 * @summary Get Admin Application Template
 */
export const getAdminApplicationTemplate = (
  templateId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<ApplicationTemplateRepresentation>>,
) => {
  return prawobiorcaRequest<ApplicationTemplateRepresentation>(
    { url: `/api/admin/application-templates/${templateId}`, method: 'GET' },
    options,
  )
}
/**
 * @summary Update Application Template
 */
export const updateApplicationTemplate = (
  templateId: string,
  applicationTemplateDetailsData: ApplicationTemplateDetailsData,
  options?: SecondParameter<typeof prawobiorcaRequest<ApplicationTemplateRepresentation>>,
) => {
  return prawobiorcaRequest<ApplicationTemplateRepresentation>(
    {
      url: `/api/admin/application-templates/${templateId}`,
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      data: applicationTemplateDetailsData,
    },
    options,
  )
}
/**
 * @summary Delete Application Template
 */
export const deleteApplicationTemplate = (
  templateId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<void>>,
) => {
  return prawobiorcaRequest<void>(
    { url: `/api/admin/application-templates/${templateId}`, method: 'DELETE' },
    options,
  )
}
/**
 * @summary Confirm Application Template Upload
 */
export const confirmApplicationTemplateUpload = (
  templateId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<ApplicationTemplateRepresentation>>,
) => {
  return prawobiorcaRequest<ApplicationTemplateRepresentation>(
    { url: `/api/admin/application-templates/${templateId}/confirm-upload`, method: 'POST' },
    options,
  )
}
/**
 * @summary Get Admin Application Template Download Url
 */
export const getAdminApplicationTemplateDownloadUrl = (
  templateId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<string>>,
) => {
  return prawobiorcaRequest<string>(
    { url: `/api/admin/application-templates/${templateId}/download-url`, method: 'GET' },
    options,
  )
}
/**
 * @summary Publish Application Template
 */
export const publishApplicationTemplate = (
  templateId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<ApplicationTemplateRepresentation>>,
) => {
  return prawobiorcaRequest<ApplicationTemplateRepresentation>(
    { url: `/api/admin/application-templates/${templateId}/publish`, method: 'POST' },
    options,
  )
}
/**
 * @summary Unpublish Application Template
 */
export const unpublishApplicationTemplate = (
  templateId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<ApplicationTemplateRepresentation>>,
) => {
  return prawobiorcaRequest<ApplicationTemplateRepresentation>(
    { url: `/api/admin/application-templates/${templateId}/unpublish`, method: 'POST' },
    options,
  )
}
export type GetPublishedApplicationTemplatesResult = NonNullable<
  Awaited<ReturnType<typeof getPublishedApplicationTemplates>>
>
export type GetApplicationTemplatesResult = NonNullable<
  Awaited<ReturnType<typeof getApplicationTemplates>>
>
export type AddApplicationTemplateResult = NonNullable<
  Awaited<ReturnType<typeof addApplicationTemplate>>
>
export type GetAdminApplicationTemplateResult = NonNullable<
  Awaited<ReturnType<typeof getAdminApplicationTemplate>>
>
export type UpdateApplicationTemplateResult = NonNullable<
  Awaited<ReturnType<typeof updateApplicationTemplate>>
>
export type DeleteApplicationTemplateResult = NonNullable<
  Awaited<ReturnType<typeof deleteApplicationTemplate>>
>
export type ConfirmApplicationTemplateUploadResult = NonNullable<
  Awaited<ReturnType<typeof confirmApplicationTemplateUpload>>
>
export type GetAdminApplicationTemplateDownloadUrlResult = NonNullable<
  Awaited<ReturnType<typeof getAdminApplicationTemplateDownloadUrl>>
>
export type PublishApplicationTemplateResult = NonNullable<
  Awaited<ReturnType<typeof publishApplicationTemplate>>
>
export type UnpublishApplicationTemplateResult = NonNullable<
  Awaited<ReturnType<typeof unpublishApplicationTemplate>>
>
