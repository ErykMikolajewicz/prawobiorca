import type { UsageTariffData } from '../../model'

import { prawobiorcaRequest } from '../../../axios'

type SecondParameter<T extends (...args: never) => unknown> = Parameters<T>[1]

/**
 * @summary Get Usage Tariff
 */
export const getUsageTariff = (
  options?: SecondParameter<typeof prawobiorcaRequest<UsageTariffData>>,
) => {
  return prawobiorcaRequest<UsageTariffData>({ url: `/api/usage-tariff`, method: 'GET' }, options)
}
/**
 * @summary Update Usage Tariff
 */
export const updateUsageTariff = (
  usageTariffData: UsageTariffData,
  options?: SecondParameter<typeof prawobiorcaRequest<void>>,
) => {
  return prawobiorcaRequest<void>(
    {
      url: `/api/usage-tariff`,
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      data: usageTariffData,
    },
    options,
  )
}
export type GetUsageTariffResult = NonNullable<Awaited<ReturnType<typeof getUsageTariff>>>
export type UpdateUsageTariffResult = NonNullable<Awaited<ReturnType<typeof updateUsageTariff>>>
