import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import MainPage from '../MainPage.vue'
import RegulationUploadDialog from '@/components/molecules/RegulationUploadDialog.vue'
import { createTestApp } from '@/__tests__/app'
import { confirmPopconfirm, findButton, findOption, page, shownMessages } from '@/__tests__/dom'
import { createHttpError, createOrganizations, createRegulation } from '@/__tests__/factories'
import {
  deleteRegulation,
  getRegulations,
  regenerateRegulationDescription,
  retryRegulationPreparation,
  searchRegulations,
  updateRegulation,
} from '@/api/generated/endpoints/regulations/regulations'
import { useAuthStore } from '@/stores/auth'
import { useOrganizationsStore } from '@/stores/organizations'
import type { RegulationRepresentation, RegulationScope } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/regulations/regulations')

type RegulationsByScope = Partial<Record<RegulationScope, Array<RegulationRepresentation>>>

function mockRegulations(regulations: RegulationsByScope) {
  vi.mocked(getRegulations).mockImplementation((params) =>
    Promise.resolve(regulations[params?.scope ?? 'PUBLIC'] ?? []),
  )
}

function logIn(isAdmin = false) {
  const authStore = useAuthStore()
  authStore.isUserLogged = true
  authStore.isAdmin = isAdmin
}

async function mountPage(path = '/', prepareStores: () => void = () => {}) {
  const { router, global } = await createTestApp(path)
  prepareStores()
  const wrapper = mount(MainPage, { global, attachTo: document.body })
  await flushPromises()
  return { router, wrapper }
}

function listTitles(wrapper: VueWrapper) {
  return wrapper.findAll('.regulations-container h2').map((title) => title.text())
}

function regulationNames(wrapper: VueWrapper, listIndex = 0) {
  const list = wrapper.findAll('.regulations-container')[listIndex]!
  return list.findAll('.regulation-name').map((name) => name.text())
}

describe('MainPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockRegulations({})
    vi.mocked(searchRegulations).mockResolvedValue([])
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('guest', () => {
    it('sees prepared public regulations and is encouraged to log in', async () => {
      mockRegulations({
        PUBLIC: [
          createRegulation({ id: 'a', presentationName: 'Ustawa o szkolnictwie' }),
          createRegulation({
            id: 'b',
            presentationName: 'W toku',
            preparationStatus: 'IN_PROGRESS',
          }),
        ],
      })

      const { wrapper } = await mountPage()

      expect(getRegulations).toHaveBeenCalledExactlyOnceWith({
        scope: 'PUBLIC',
        documentType: undefined,
        organizationId: undefined,
        suborganizationId: undefined,
      })
      expect(listTitles(wrapper)).toEqual(['Publiczne regulacje'])
      expect(regulationNames(wrapper)).toEqual(['Ustawa o szkolnictwie'])
      expect(wrapper.text()).toContain('Jak to działa?')
      expect(wrapper.find('.login-cta-banner').exists()).toBe(true)
      expect(findButton('Dodaj regulacje')).toBeUndefined()
    })

    it('explains the three steps for finding legal provisions', async () => {
      const { wrapper } = await mountPage()

      expect(
        wrapper
          .findAll('.how-it-works .step')
          .map((step) => [
            step.find('.feature-item-title').text(),
            step.find('.feature-item-description').text(),
          ]),
      ).toEqual([
        ['1. Wybierz akt prawny', 'Kliknij regulację z listy poniżej.'],
        ['2. Zadaj pytanie', 'Napisz, czego chciałbyś się dowiedzieć.'],
        ['3. Poznaj przepisy', 'Zobacz artykuły, które najlepiej pasują do pytania.'],
      ])
    })

    it('labels regulations with their type', async () => {
      mockRegulations({
        PUBLIC: [
          createRegulation({ id: 'a', presentationName: 'A', regulationType: 'ACT' }),
          createRegulation({ id: 'b', presentationName: 'B', regulationType: null }),
        ],
      })

      const { wrapper } = await mountPage()

      const [typedRegulation, untypedRegulation] = wrapper.findAll('.regulation-item')
      expect(typedRegulation!.find('.app-badge .label:not(.is-hidden)').text()).toBe('Ustawa')
      expect(untypedRegulation!.find('.app-badge').exists()).toBe(false)
    })

    it('hides the login banner for the rest of the day after closing it', async () => {
      const firstVisit = await mountPage()
      await firstVisit.wrapper.find('.login-cta-banner button[title="Zamknij"]').trigger('click')
      expect(firstVisit.wrapper.find('.login-cta-banner').exists()).toBe(false)
      firstVisit.wrapper.unmount()

      const secondVisit = await mountPage()
      expect(secondVisit.wrapper.find('.login-cta-banner').exists()).toBe(false)
    })

    it('shows the login banner again on another day', async () => {
      localStorage.setItem('login-cta-dismissed-on', new Date(2020, 0, 1).toDateString())

      const { wrapper } = await mountPage()

      expect(wrapper.find('.login-cta-banner').exists()).toBe(true)
    })

    it.each([
      ['Zaloguj się', 'LoginPage'],
      ['Załóż konto', 'RegisterPage'],
    ])('opens the page behind the banner button "%s"', async (label, routeName) => {
      const { router } = await mountPage()

      await findButton(label)!.trigger('click')
      await flushPromises()

      expect(router.currentRoute.value.name).toBe(routeName)
    })

    it('informs that there are no public regulations', async () => {
      const { wrapper } = await mountPage()

      expect(wrapper.find('.regulations-container').text()).toContain('Brak regulacji publicznych.')
    })

    it('reports public regulations that could not be loaded', async () => {
      vi.spyOn(console, 'error').mockImplementationOnce(() => {})
      vi.mocked(getRegulations).mockRejectedValue(createHttpError(500))

      await mountPage()

      expect(shownMessages('error')).toEqual(['Nie udało się pobrać regulacji publicznych.'])
    })
  })

  describe('logged user', () => {
    it('sees public regulations and all own regulations with their status', async () => {
      mockRegulations({
        PUBLIC: [
          createRegulation({ id: 'a', presentationName: 'Ustawa o szkolnictwie' }),
          createRegulation({
            id: 'b',
            presentationName: 'W toku',
            preparationStatus: 'IN_PROGRESS',
          }),
        ],
        PRIVATE: [
          createRegulation({ id: 'c', presentationName: 'Moje notatki' }),
          createRegulation({ id: 'd', presentationName: 'Skan', preparationStatus: 'FAILED' }),
        ],
      })

      const { wrapper } = await mountPage('/', logIn)

      expect(getRegulations).toHaveBeenCalledWith({ scope: 'PRIVATE', documentType: undefined })
      expect(listTitles(wrapper)).toEqual(['Publiczne regulacje', 'Regulacje użytkownika'])
      expect(regulationNames(wrapper, 0)).toEqual(['Ustawa o szkolnictwie'])
      expect(regulationNames(wrapper, 1)).toEqual(['Moje notatki', 'Skan'])
      expect(wrapper.findAll('.regulations-container')[1]!.text()).toContain('Błąd przetwarzania')
      expect(wrapper.find('.login-cta-banner').exists()).toBe(false)
      expect(wrapper.text()).not.toContain('Jak to działa?')
    })

    it('opens the upload dialog', async () => {
      await mountPage('/', logIn)

      await findButton('Dodaj regulacje')!.trigger('click')

      expect(page().find('.el-dialog').text()).toContain('Dodaj plik')
    })

    it.each([
      ['PUBLIC', 0],
      ['PRIVATE', 1],
    ] as const)('shows an uploaded %s regulation on its list', async (target, listIndex) => {
      const { wrapper } = await mountPage('/', () => logIn(true))
      const regulation = createRegulation({ presentationName: 'Nowy regulamin' })

      wrapper.findComponent(RegulationUploadDialog).vm.$emit('created', regulation, target)
      await flushPromises()

      expect(regulationNames(wrapper, listIndex)).toEqual(['Nowy regulamin'])
      expect(regulationNames(wrapper, 1 - listIndex)).toEqual([])
    })

    it('renames a regulation edited in its details', async () => {
      const regulation = createRegulation({ presentationName: 'Moje notatki' })
      mockRegulations({ PRIVATE: [regulation] })
      vi.mocked(updateRegulation).mockResolvedValue({ ...regulation, presentationName: 'Notatki' })
      const { wrapper } = await mountPage('/', logIn)

      await wrapper.find('button[aria-label="Opcje regulacji"]').trigger('click')
      await page().find('input[placeholder="Nazwa regulacji"]').setValue('Notatki')
      await findButton('Zapisz')!.trigger('click')
      await flushPromises()

      expect(updateRegulation).toHaveBeenCalledExactlyOnceWith('regulation-1', {
        name: 'Notatki',
        description: null,
      })
      expect(regulationNames(wrapper, 1)).toEqual(['Notatki'])
    })

    it('removes a regulation deleted in its details', async () => {
      mockRegulations({ PRIVATE: [createRegulation()] })
      const { wrapper } = await mountPage('/', logIn)

      await wrapper.find('button[aria-label="Opcje regulacji"]').trigger('click')
      await findButton('Usuń')!.trigger('click')
      await confirmPopconfirm()
      await flushPromises()

      expect(deleteRegulation).toHaveBeenCalledExactlyOnceWith('regulation-1')
      expect(regulationNames(wrapper, 1)).toEqual([])
    })

    it('shows a regulation as being processed after retrying its preparation', async () => {
      mockRegulations({ PRIVATE: [createRegulation({ preparationStatus: 'FAILED' })] })
      const { wrapper } = await mountPage('/', logIn)

      await wrapper.find('button[aria-label="Ponów przetwarzanie"]').trigger('click')
      await flushPromises()

      expect(retryRegulationPreparation).toHaveBeenCalledExactlyOnceWith('regulation-1')
      expect(wrapper.find('.regulation-item').text()).toContain('Przetwarzanie')
      expect(wrapper.find('button[aria-label="Ponów przetwarzanie"]').exists()).toBe(false)
    })

    it('refreshes regulations being processed until they are prepared', async () => {
      vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'Date'] })
      mockRegulations({ PRIVATE: [createRegulation({ preparationStatus: 'IN_PROGRESS' })] })
      const { wrapper } = await mountPage('/', logIn)
      expect(wrapper.find('a.regulation-link').exists()).toBe(false)

      mockRegulations({ PRIVATE: [createRegulation({ preparationStatus: 'PREPARED' })] })
      await vi.advanceTimersByTimeAsync(5000)
      await flushPromises()

      expect(wrapper.find('a.regulation-link').attributes('href')).toBe(
        '/user/regulations/regulation-1/documents',
      )

      vi.mocked(getRegulations).mockClear()
      await vi.advanceTimersByTimeAsync(30_000)
      expect(getRegulations).not.toHaveBeenCalled()
    })

    it('keeps the lists when a background refresh fails', async () => {
      vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'Date'] })
      vi.spyOn(console, 'error').mockImplementationOnce(() => {})
      mockRegulations({ PRIVATE: [createRegulation({ preparationStatus: 'IN_PROGRESS' })] })
      const { wrapper } = await mountPage('/', logIn)

      vi.mocked(getRegulations).mockRejectedValue(createHttpError(503))
      await vi.advanceTimersByTimeAsync(5000)
      await flushPromises()

      expect(regulationNames(wrapper, 1)).toEqual(['Regulamin studiów'])
      expect(shownMessages('error')).toEqual([])
    })

    it('does not refresh because of public regulations it cannot manage', async () => {
      vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'Date'] })
      mockRegulations({ PUBLIC: [createRegulation({ preparationStatus: 'IN_PROGRESS' })] })
      await mountPage('/', logIn)
      vi.mocked(getRegulations).mockClear()

      await vi.advanceTimersByTimeAsync(30_000)

      expect(getRegulations).not.toHaveBeenCalled()
    })
  })

  describe('administrator', () => {
    it('sees public regulations that are not prepared yet', async () => {
      mockRegulations({
        PUBLIC: [
          createRegulation({ presentationName: 'W toku', preparationStatus: 'IN_PROGRESS' }),
        ],
      })

      const { wrapper } = await mountPage('/', () => logIn(true))

      expect(regulationNames(wrapper, 0)).toEqual(['W toku'])
      expect(wrapper.find('.regulation-item').text()).toContain('Przetwarzanie')
    })

    it('refreshes public regulations being processed', async () => {
      vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'Date'] })
      mockRegulations({ PUBLIC: [createRegulation({ preparationStatus: 'IN_PROGRESS' })] })
      const { wrapper } = await mountPage('/', () => logIn(true))

      mockRegulations({ PUBLIC: [createRegulation({ preparationStatus: 'PREPARED' })] })
      await vi.advanceTimersByTimeAsync(5000)
      await flushPromises()

      expect(wrapper.find('a.regulation-link').attributes('href')).toBe(
        '/regulations/regulation-1/documents',
      )
    })

    it('shows the description of a public regulation as being generated after starting it', async () => {
      mockRegulations({ PUBLIC: [createRegulation()] })
      const { wrapper } = await mountPage('/', () => logIn(true))

      await wrapper.find('button[aria-label="Opcje regulacji"]').trigger('click')
      await findButton('Wygeneruj opis przez AI')!.trigger('click')
      await flushPromises()

      expect(regenerateRegulationDescription).toHaveBeenCalledExactlyOnceWith('regulation-1')
      expect(page().find('.el-dialog').text()).toContain('Generowanie opisu')
      expect(findButton('Wygeneruj opis przez AI')).toBeUndefined()
    })
  })

  describe('search', () => {
    const searchResults = [
      { regulation: createRegulation({ id: 'a', presentationName: 'Statut' }), score: 0.9 },
      { regulation: createRegulation({ id: 'b', presentationName: 'Regulamin' }), score: 0.7 },
    ]

    it('searches regulations by description and keeps the search in the address', async () => {
      vi.mocked(searchRegulations).mockResolvedValue(searchResults)
      const { router, wrapper } = await mountPage()

      await wrapper.find('input[placeholder^="Opisz sprawę"]').setValue(' urlop dziekański ')
      await wrapper.find('form').trigger('submit')
      await flushPromises()

      expect(searchRegulations).toHaveBeenCalledExactlyOnceWith({
        scope: 'PUBLIC',
        documentType: undefined,
        organizationId: undefined,
        suborganizationId: undefined,
        query: 'urlop dziekański',
        threshold: 0.5,
      })
      expect(router.currentRoute.value.query).toEqual({
        query: 'urlop dziekański',
        threshold: '0.5',
        orderBy: 'name',
      })
      expect(regulationNames(wrapper)).toEqual(['Regulamin', 'Statut'])
      expect(wrapper.find('.regulation-score').text()).toBe('Podobieństwo: 0.700')
    })

    it('repeats the search from the address for public and own regulations', async () => {
      vi.mocked(searchRegulations).mockResolvedValue(searchResults)

      const { wrapper } = await mountPage('/?query=urlop&threshold=0.6&orderBy=score', logIn)

      expect(getRegulations).not.toHaveBeenCalled()
      expect(searchRegulations).toHaveBeenCalledWith(
        expect.objectContaining({ scope: 'PUBLIC', query: 'urlop', threshold: 0.6 }),
      )
      expect(searchRegulations).toHaveBeenCalledWith({
        scope: 'PRIVATE',
        documentType: undefined,
        query: 'urlop',
        threshold: 0.6,
      })
      expect(regulationNames(wrapper, 0)).toEqual(['Statut', 'Regulamin'])
    })

    it('reorders found regulations without searching again', async () => {
      vi.mocked(searchRegulations).mockResolvedValue(searchResults)
      const { router, wrapper } = await mountPage('/?query=urlop')
      expect(regulationNames(wrapper)).toEqual(['Regulamin', 'Statut'])

      await wrapper.find('input[type="radio"][value="score"]').setValue(true)
      await flushPromises()

      expect(regulationNames(wrapper)).toEqual(['Statut', 'Regulamin'])
      expect(router.currentRoute.value.query.orderBy).toBe('score')
      expect(searchRegulations).toHaveBeenCalledTimes(1)
    })

    it('informs that no regulation matches the query', async () => {
      const { wrapper } = await mountPage('/?query=urlop')

      expect(wrapper.find('.regulations-container').text()).toContain(
        'Brak regulacji pasujących do zapytania.',
      )
    })

    it('lists all regulations again and cleans the address after clearing the query', async () => {
      mockRegulations({ PUBLIC: [createRegulation({ presentationName: 'Statut' })] })
      const { router, wrapper } = await mountPage('/?query=urlop&orderBy=score')
      expect(regulationNames(wrapper)).toEqual([])

      await wrapper.find('input[placeholder^="Opisz sprawę"]').setValue('')
      await wrapper.find('form').trigger('submit')
      await flushPromises()

      expect(router.currentRoute.value.query).toEqual({})
      expect(regulationNames(wrapper)).toEqual(['Statut'])
    })
  })

  describe('filters', () => {
    it('reloads public regulations of the chosen type', async () => {
      await mountPage()

      await findOption('Ustawa')!.trigger('click')
      await flushPromises()

      expect(getRegulations).toHaveBeenLastCalledWith(
        expect.objectContaining({ scope: 'PUBLIC', documentType: 'ACT' }),
      )
    })

    it('reloads public regulations of the chosen organization and suborganization', async () => {
      const { wrapper } = await mountPage('/', () => {
        useOrganizationsStore().organizations = createOrganizations()
      })
      const suborganizationFilter = wrapper.findAll(
        '.regulation-organization-filter .el-select__wrapper',
      )[1]!
      expect(suborganizationFilter.classes()).toContain('is-disabled')

      await findOption('Politechnika Wrocławska')!.trigger('click')
      await flushPromises()
      expect(suborganizationFilter.classes()).not.toContain('is-disabled')
      expect(getRegulations).toHaveBeenLastCalledWith(
        expect.objectContaining({ organizationId: 'pwr', suborganizationId: undefined }),
      )

      await findOption('Wydział Mechaniczny')!.trigger('click')
      await flushPromises()
      expect(getRegulations).toHaveBeenLastCalledWith(
        expect.objectContaining({ organizationId: 'pwr', suborganizationId: 'w10' }),
      )

      await findOption('Uniwersytet Wrocławski')!.trigger('click')
      await flushPromises()
      expect(getRegulations).toHaveBeenLastCalledWith(
        expect.objectContaining({ organizationId: 'uwr', suborganizationId: undefined }),
      )
    })
  })
})
