import type { CreatedOAuthClient, NewOAuthClient, OAuthClientData } from '../../model'

import { prawobiorcaRequest } from '../../../axios'

type SecondParameter<T extends (...args: never) => unknown> = Parameters<T>[1]

/**
 * @summary Get Oauth Clients
 */
export const getOauthClients = (
  options?: SecondParameter<typeof prawobiorcaRequest<OAuthClientData[]>>,
) => {
  return prawobiorcaRequest<OAuthClientData[]>(
    { url: `/api/oauth-clients`, method: 'GET' },
    options,
  )
}
/**
 * @summary Create Oauth Client
 */
export const createOauthClient = (
  newOAuthClient: NewOAuthClient,
  options?: SecondParameter<typeof prawobiorcaRequest<CreatedOAuthClient>>,
) => {
  return prawobiorcaRequest<CreatedOAuthClient>(
    {
      url: `/api/oauth-clients`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      data: newOAuthClient,
    },
    options,
  )
}
/**
 * @summary Delete Oauth Client
 */
export const deleteOauthClient = (
  clientId: string,
  options?: SecondParameter<typeof prawobiorcaRequest<void>>,
) => {
  return prawobiorcaRequest<void>(
    { url: `/api/oauth-clients/${clientId}`, method: 'DELETE' },
    options,
  )
}
export type GetOauthClientsResult = NonNullable<Awaited<ReturnType<typeof getOauthClients>>>
export type CreateOauthClientResult = NonNullable<Awaited<ReturnType<typeof createOauthClient>>>
export type DeleteOauthClientResult = NonNullable<Awaited<ReturnType<typeof deleteOauthClient>>>
