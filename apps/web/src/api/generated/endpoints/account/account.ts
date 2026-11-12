import type { RegistrationData } from '../../model'

import { prawobiorcaRequest } from '../../../axios'

type SecondParameter<T extends (...args: never) => unknown> = Parameters<T>[1]

/**
 * @summary Create Account
 */
export const createAccount = (
  registrationData: RegistrationData,
  options?: SecondParameter<typeof prawobiorcaRequest<unknown>>,
) => {
  return prawobiorcaRequest<unknown>(
    {
      url: `/api/accounts/register`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      data: registrationData,
    },
    options,
  )
}
export type CreateAccountResult = NonNullable<Awaited<ReturnType<typeof createAccount>>>
