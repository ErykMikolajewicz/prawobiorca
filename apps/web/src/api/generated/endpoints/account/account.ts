import type { LoginData } from '../../model'

import { prawobiorcaRequest } from '../../../axios'

type SecondParameter<T extends (...args: never) => unknown> = Parameters<T>[1]

/**
 * @summary Create Account
 */
export const createAccount = (
  loginData: LoginData,
  options?: SecondParameter<typeof prawobiorcaRequest<unknown>>,
) => {
  return prawobiorcaRequest<unknown>(
    {
      url: `/api/accounts/register`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      data: loginData,
    },
    options,
  )
}
export type CreateAccountResult = NonNullable<Awaited<ReturnType<typeof createAccount>>>
