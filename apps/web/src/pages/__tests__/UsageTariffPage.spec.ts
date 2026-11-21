import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import UsageTariffPage from '../UsageTariffPage.vue'
import { createTestApp } from '@/__tests__/app'
import { findButton, shownMessages } from '@/__tests__/dom'
import { createHttpError } from '@/__tests__/factories'
import { getUsageTariff, updateUsageTariff } from '@/api/generated/endpoints/usage/usage'

import type { UsageTariffData } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/usage/usage')

const TARIFF: UsageTariffData = {
  semanticSearchPrice: 0.03,
  applicationGenerationPrice: 0.5,
  regulationPreparationPrice: 1,
  accountDailyLimit: 5,
  anonymousIpDailyLimit: 2,
  anonymousTotalDailyLimit: 50,
}

async function mountPage() {
  const { global } = await createTestApp('/admin/usage-tariff')
  const wrapper = mount(UsageTariffPage, { global, attachTo: document.body })
  await flushPromises()
  return wrapper
}

function findField(wrapper: Awaited<ReturnType<typeof mountPage>>, label: string) {
  const item = wrapper.findAll('.el-form-item').find((formItem) => formItem.text().includes(label))!
  return item.find('input')
}

async function save() {
  await findButton('Zapisz')!.trigger('click')
  await flushPromises()
}

describe('UsageTariffPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.mocked(getUsageTariff).mockResolvedValue({ ...TARIFF })
  })

  it('shows the current prices and daily budgets', async () => {
    const wrapper = await mountPage()

    expect((findField(wrapper, 'Wyszukiwanie semantyczne').element as HTMLInputElement).value).toBe(
      '0.03',
    )
    expect((findField(wrapper, 'Wszyscy goście łącznie').element as HTMLInputElement).value).toBe(
      '50.00',
    )
  })

  it('saves the changed values', async () => {
    const wrapper = await mountPage()

    const accountLimit = findField(wrapper, 'Konto użytkownika')
    await accountLimit.setValue('7.5')
    await accountLimit.trigger('change')
    await save()

    expect(updateUsageTariff).toHaveBeenCalledExactlyOnceWith({ ...TARIFF, accountDailyLimit: 7.5 })
    expect(shownMessages('success')).toEqual(['Zmiany zostały zapisane.'])
  })

  it('does not accept a negative value', async () => {
    const wrapper = await mountPage()

    const searchPrice = findField(wrapper, 'Wyszukiwanie semantyczne')
    await searchPrice.setValue('-1')
    await searchPrice.trigger('change')
    await save()

    expect(updateUsageTariff).toHaveBeenCalledExactlyOnceWith({ ...TARIFF, semanticSearchPrice: 0 })
  })

  it('informs when saving fails', async () => {
    vi.mocked(updateUsageTariff).mockRejectedValue(createHttpError(500))
    await mountPage()

    await save()

    expect(shownMessages('error')).toEqual(['Nie udało się zapisać zmian.'])
    expect(shownMessages('success')).toEqual([])
  })

  it('informs when the tariff can not be loaded', async () => {
    vi.mocked(getUsageTariff).mockRejectedValue(createHttpError(500))
    const wrapper = await mountPage()

    expect(shownMessages('error')).toEqual(['Nie udało się pobrać cennika.'])
    expect(wrapper.find('form').exists()).toBe(false)
    expect(wrapper.text()).toContain('Nie udało się pobrać cennika.')
  })
})
