import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import SearchPage from '../SearchPage.vue'
import SearchResultsList from '@/components/organisms/SearchResultsList.vue'
import { createTestApp } from '@/__tests__/app'
import { findButton, shownMessages } from '@/__tests__/dom'
import { createHttpError, createRegulation, createSearchResult } from '@/__tests__/factories'
import { addCaseDocument } from '@/api/generated/endpoints/cases/cases'
import {
  getRegulationById,
  searchRegulationDocuments,
} from '@/api/generated/endpoints/regulations/regulations'
import { useAuthStore } from '@/stores/auth'
import { useCasesStore } from '@/stores/cases'

vi.mock('@/api/generated/endpoints/cases/cases')
vi.mock('@/api/generated/endpoints/regulations/regulations')

const PAGE_PATH = '/regulations/regulation-1/documents'

async function mountPage(path = PAGE_PATH, prepareStores: () => void = () => {}) {
  const { router, global } = await createTestApp(path)
  prepareStores()
  const wrapper = mount(SearchPage, { global, attachTo: document.body })
  await flushPromises()
  return { router, wrapper }
}

function logInWithActiveCase() {
  useAuthStore().isUserLogged = true
  useCasesStore().add({ id: 'case-1', name: 'Urlop dziekański' })
}

async function search(wrapper: Awaited<ReturnType<typeof mountPage>>['wrapper'], query: string) {
  await wrapper.find('input[placeholder="Wpisz treść..."]').setValue(query)
  await wrapper.find('form').trigger('submit')
  await flushPromises()
}

describe('SearchPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.mocked(getRegulationById).mockResolvedValue(createRegulation())
    vi.mocked(searchRegulationDocuments).mockResolvedValue([createSearchResult()])
  })

  it('shows the name of the regulation from the address', async () => {
    const { wrapper } = await mountPage()

    expect(getRegulationById).toHaveBeenCalledExactlyOnceWith('regulation-1')
    expect(wrapper.find('h1').text()).toBe('Przeszukaj regulacje: Regulamin studiów')
  })

  it('reports a regulation that could not be loaded', async () => {
    vi.mocked(getRegulationById).mockRejectedValue(createHttpError(404))

    await mountPage()

    expect(shownMessages('error')).toEqual(['Nie udało się pobrać regulacji.'])
  })

  it('does not search until a query is given', async () => {
    const { wrapper } = await mountPage()

    await search(wrapper, '   ')

    expect(searchRegulationDocuments).not.toHaveBeenCalled()
    expect(wrapper.find('.search-results').text()).toBe('')
  })

  it('searches the regulation and keeps the search in the address', async () => {
    const { router, wrapper } = await mountPage()

    await search(wrapper, 'urlop zdrowotny')

    expect(searchRegulationDocuments).toHaveBeenCalledExactlyOnceWith('regulation-1', {
      query: 'urlop zdrowotny',
      threshold: 0.5,
      limit: 10,
      order_by: 'score',
    })
    expect(router.currentRoute.value.query).toEqual({
      query: 'urlop zdrowotny',
      threshold: '0.5',
      limit: '10',
      order_by: 'score',
    })
    expect(wrapper.find('.result-group-header').text()).toBe('§ 12')
    expect(wrapper.find('.result-line').text()).toBe('1. Student ma prawo do urlopu.')
  })

  it('repeats the search from the address', async () => {
    await mountPage(`${PAGE_PATH}?query=urlop&threshold=0.7&limit=5&order_by=document`)

    expect(searchRegulationDocuments).toHaveBeenCalledExactlyOnceWith('regulation-1', {
      query: 'urlop',
      threshold: 0.7,
      limit: 5,
      order_by: 'document',
    })
  })

  it('searches again when the order of results is changed', async () => {
    const { wrapper } = await mountPage(`${PAGE_PATH}?query=urlop`)

    await wrapper.find('input[type="radio"][value="document"]').setValue(true)
    await flushPromises()

    expect(searchRegulationDocuments).toHaveBeenLastCalledWith(
      'regulation-1',
      expect.objectContaining({ query: 'urlop', order_by: 'document' }),
    )
  })

  it('informs that nothing matches the query', async () => {
    vi.mocked(searchRegulationDocuments).mockResolvedValue([])
    const { wrapper } = await mountPage()

    await search(wrapper, 'urlop')

    expect(wrapper.find('.search-results').text()).toBe('Brak wyników dla zapytania: "urlop"')
  })

  it('reports a failed search', async () => {
    vi.mocked(searchRegulationDocuments).mockRejectedValue(createHttpError(503))
    const { wrapper } = await mountPage()

    await search(wrapper, 'urlop')

    expect(shownMessages('error')).toEqual([
      'Serwis jest chwilowo niedostępny. Spróbuj ponownie później.',
    ])
  })

  it('does not offer adding results to a case to a guest', async () => {
    await mountPage(`${PAGE_PATH}?query=urlop`)

    expect(findButton('Dodaj do sprawy')).toBeUndefined()
  })

  it('adds a result to the active case', async () => {
    const result = createSearchResult({ highlight: { start_element: 0, end_element: 0 } })
    vi.mocked(searchRegulationDocuments).mockResolvedValue([result])
    await mountPage(`${PAGE_PATH}?query=urlop`, logInWithActiveCase)

    await findButton('Dodaj do sprawy')!.trigger('click')
    await flushPromises()

    expect(addCaseDocument).toHaveBeenCalledExactlyOnceWith('case-1', {
      presentationName: 'Regulamin studiów',
      content: result.text,
      header: result.header,
      elements: result.elements,
      highlight: result.highlight,
    })
    expect(shownMessages('success')).toEqual(['Dodano do sprawy: Urlop dziekański'])
  })

  it('reports a result that could not be added to the case', async () => {
    vi.mocked(addCaseDocument).mockRejectedValue(createHttpError(500))
    await mountPage(`${PAGE_PATH}?query=urlop`, logInWithActiveCase)

    await findButton('Dodaj do sprawy')!.trigger('click')
    await flushPromises()

    expect(shownMessages('error')).toEqual(['Wystąpił błąd podczas dodawania do sprawy.'])
    expect(shownMessages('success')).toEqual([])
  })

  it('blocks adding results until a case is set as active', async () => {
    await mountPage(`${PAGE_PATH}?query=urlop`, () => {
      useAuthStore().isUserLogged = true
    })

    expect(findButton('Dodaj do sprawy')!.attributes('disabled')).toBeDefined()
  })

  it('asks to choose a case when a result is added without an active one', async () => {
    const result = createSearchResult()
    const { wrapper } = await mountPage(`${PAGE_PATH}?query=urlop`, () => {
      useAuthStore().isUserLogged = true
    })

    wrapper.findComponent(SearchResultsList).vm.$emit('add-to-case', {
      documentContent: result.text,
      header: result.header,
      elements: result.elements,
      highlight: result.highlight,
    })
    await flushPromises()

    expect(shownMessages('warning')).toEqual(['Wybierz aktywną sprawę w panelu bocznym.'])
    expect(addCaseDocument).not.toHaveBeenCalled()
  })

  it('offers the advanced relevance level only to a logged user', async () => {
    const guestPage = await mountPage()
    expect(guestPage.wrapper.text()).not.toContain('Zaawansowane')
    guestPage.wrapper.unmount()

    const userPage = await mountPage(PAGE_PATH, () => {
      useAuthStore().isUserLogged = true
    })
    expect(userPage.wrapper.text()).toContain('Zaawansowane')
  })
})
