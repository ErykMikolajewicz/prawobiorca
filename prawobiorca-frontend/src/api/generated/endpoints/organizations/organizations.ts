import type { NewOrganization, NewSuborganization, OrganizationData } from '../../model'

import { prawobiorcaRequest } from '../../../axios'

type SecondParameter<T extends (...args: never) => unknown> = Parameters<T>[1]

/**
 * @summary Get Organizations
 */
export const getOrganizations = (
  options?: SecondParameter<typeof prawobiorcaRequest<OrganizationData[]>>,
) => {
  return prawobiorcaRequest<OrganizationData[]>(
    { url: `/api/organizations`, method: 'GET' },
    options,
  )
}
/**
 * @summary Add Organization
 */
export const addOrganization = (
  newOrganization: NewOrganization,
  options?: SecondParameter<typeof prawobiorcaRequest<string>>,
) => {
  return prawobiorcaRequest<string>(
    {
      url: `/api/admin/organizations`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      data: newOrganization,
    },
    options,
  )
}
/**
 * @summary Update Organization
 */
export const updateOrganization = (
  organizationId: string,
  newOrganization: NewOrganization,
  options?: SecondParameter<typeof prawobiorcaRequest<void>>,
) => {
  return prawobiorcaRequest<void>(
    {
      url: `/api/admin/organizations/${organizationId}`,
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      data: newOrganization,
    },
    options,
  )
}
/**
 * @summary Delete Organization
 */
export const deleteOrganization = (
  organizationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<void>>,
) => {
  return prawobiorcaRequest<void>(
    { url: `/api/admin/organizations/${organizationId}`, method: 'DELETE' },
    options,
  )
}
/**
 * @summary Add Suborganization
 */
export const addSuborganization = (
  organizationId: string,
  newSuborganization: NewSuborganization,
  options?: SecondParameter<typeof prawobiorcaRequest<string>>,
) => {
  return prawobiorcaRequest<string>(
    {
      url: `/api/admin/organizations/${organizationId}/suborganizations`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      data: newSuborganization,
    },
    options,
  )
}
/**
 * @summary Update Suborganization
 */
export const updateSuborganization = (
  suborganizationId: string,
  newSuborganization: NewSuborganization,
  options?: SecondParameter<typeof prawobiorcaRequest<void>>,
) => {
  return prawobiorcaRequest<void>(
    {
      url: `/api/admin/suborganizations/${suborganizationId}`,
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      data: newSuborganization,
    },
    options,
  )
}
/**
 * @summary Delete Suborganization
 */
export const deleteSuborganization = (
  suborganizationId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<void>>,
) => {
  return prawobiorcaRequest<void>(
    { url: `/api/admin/suborganizations/${suborganizationId}`, method: 'DELETE' },
    options,
  )
}
export type GetOrganizationsResult = NonNullable<Awaited<ReturnType<typeof getOrganizations>>>
export type AddOrganizationResult = NonNullable<Awaited<ReturnType<typeof addOrganization>>>
export type UpdateOrganizationResult = NonNullable<Awaited<ReturnType<typeof updateOrganization>>>
export type DeleteOrganizationResult = NonNullable<Awaited<ReturnType<typeof deleteOrganization>>>
export type AddSuborganizationResult = NonNullable<Awaited<ReturnType<typeof addSuborganization>>>
export type UpdateSuborganizationResult = NonNullable<
  Awaited<ReturnType<typeof updateSuborganization>>
>
export type DeleteSuborganizationResult = NonNullable<
  Awaited<ReturnType<typeof deleteSuborganization>>
>
