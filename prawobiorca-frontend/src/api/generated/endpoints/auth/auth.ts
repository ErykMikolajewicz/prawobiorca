import type { BodyLogUser } from '../../model'

import { prawobiorcaRequest } from '../../../axios'

type SecondParameter<T extends (...args: never) => unknown> = Parameters<T>[1]

/**
 * @summary Log User
 */
export const logUser = (
  bodyLogUser: BodyLogUser,
  options?: SecondParameter<typeof prawobiorcaRequest<unknown>>,
) => {
  const formUrlEncoded = new URLSearchParams()
  if (bodyLogUser.grant_type !== undefined && bodyLogUser.grant_type !== null) {
    formUrlEncoded.append(`grant_type`, bodyLogUser.grant_type)
  }
  formUrlEncoded.append(`username`, bodyLogUser.username)
  formUrlEncoded.append(`password`, bodyLogUser.password)
  if (bodyLogUser.scope !== undefined) {
    formUrlEncoded.append(`scope`, bodyLogUser.scope)
  }
  if (bodyLogUser.client_id !== undefined && bodyLogUser.client_id !== null) {
    formUrlEncoded.append(`client_id`, bodyLogUser.client_id)
  }
  if (bodyLogUser.client_secret !== undefined && bodyLogUser.client_secret !== null) {
    formUrlEncoded.append(`client_secret`, bodyLogUser.client_secret)
  }

  return prawobiorcaRequest<unknown>(
    {
      url: `/api/auth/login`,
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      data: formUrlEncoded,
    },
    options,
  )
}
/**
 * @summary Refresh Tokens
 */
export const refreshTokens = (options?: SecondParameter<typeof prawobiorcaRequest<unknown>>) => {
  return prawobiorcaRequest<unknown>({ url: `/api/auth/refresh`, method: 'POST' }, options)
}
/**
 * @summary Check Is User Logged
 */
export const checkIsUserLogged = (
  options?: SecondParameter<typeof prawobiorcaRequest<unknown>>,
) => {
  return prawobiorcaRequest<unknown>({ url: `/api/auth/me`, method: 'GET' }, options)
}
/**
 * @summary Logout User
 */
export const logoutUser = (options?: SecondParameter<typeof prawobiorcaRequest<unknown>>) => {
  return prawobiorcaRequest<unknown>({ url: `/api/auth/logout`, method: 'POST' }, options)
}
export type LogUserResult = NonNullable<Awaited<ReturnType<typeof logUser>>>
export type RefreshTokensResult = NonNullable<Awaited<ReturnType<typeof refreshTokens>>>
export type CheckIsUserLoggedResult = NonNullable<Awaited<ReturnType<typeof checkIsUserLogged>>>
export type LogoutUserResult = NonNullable<Awaited<ReturnType<typeof logoutUser>>>
