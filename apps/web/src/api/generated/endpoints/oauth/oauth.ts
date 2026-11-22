import type {
  AuthorizationRedirect,
  AuthorizationRequest,
  AuthorizationRequestDetails,
  GetConsentDetailsParams,
} from '../../model'

import { prawobiorcaRequest } from '../../../axios'

type SecondParameter<T extends (...args: never) => unknown> = Parameters<T>[1]

/**
 * @summary Get Consent Details
 */
export const getConsentDetails = (
  params: GetConsentDetailsParams,
  options?: SecondParameter<typeof prawobiorcaRequest<AuthorizationRequestDetails>>,
) => {
  return prawobiorcaRequest<AuthorizationRequestDetails>(
    { url: `/api/oauth/consent`, method: 'GET', params },
    options,
  )
}
/**
 * @summary Grant Consent
 */
export const grantConsent = (
  authorizationRequest: AuthorizationRequest,
  options?: SecondParameter<typeof prawobiorcaRequest<AuthorizationRedirect>>,
) => {
  return prawobiorcaRequest<AuthorizationRedirect>(
    {
      url: `/api/oauth/consent`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      data: authorizationRequest,
    },
    options,
  )
}
export type GetConsentDetailsResult = NonNullable<Awaited<ReturnType<typeof getConsentDetails>>>
export type GrantConsentResult = NonNullable<Awaited<ReturnType<typeof grantConsent>>>
