import { describe, it, expect } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import FeaturesPage from '../FeaturesPage.vue'
import { createTestApp } from '@/__tests__/app'
import { findButton } from '@/__tests__/dom'
import { useAuthStore } from '@/stores/auth'

async function mountPage(isUserLogged: boolean) {
  const { router, global } = await createTestApp('/features')
  useAuthStore().isUserLogged = isUserLogged
  const wrapper = mount(FeaturesPage, { global, attachTo: document.body })
  return { router, wrapper }
}

describe('FeaturesPage', () => {
  it('describes the features available after logging in', async () => {
    const { wrapper } = await mountPage(false)

    expect(wrapper.findAll('.feature-item-title').map((title) => title.text())).toEqual([
      'Zarządzanie sprawami',
      'Generowanie wniosków',
      'Własne regulacje',
    ])
  })

  it.each([
    ['Zaloguj się', 'LoginPage'],
    ['Załóż konto', 'RegisterPage'],
  ])('leads a guest to "%s"', async (label, routeName) => {
    const { router } = await mountPage(false)

    await findButton(label)!.trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.name).toBe(routeName)
  })

  it('does not encourage a logged user to log in', async () => {
    await mountPage(true)

    expect(findButton('Zaloguj się')).toBeUndefined()
    expect(findButton('Załóż konto')).toBeUndefined()
  })
})
