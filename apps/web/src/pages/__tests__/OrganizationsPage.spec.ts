import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount, type DOMWrapper } from '@vue/test-utils'
import OrganizationsPage from '../OrganizationsPage.vue'
import { createTestApp } from '@/__tests__/app'
import { confirmPopconfirm, findButton, shownMessages } from '@/__tests__/dom'
import { createFailingRequest, createHttpError, createOrganizations } from '@/__tests__/factories'
import {
  addOrganization,
  addSuborganization,
  deleteOrganization,
  deleteSuborganization,
  getOrganizations,
  updateOrganization,
  updateSuborganization,
} from '@/api/generated/endpoints/organizations/organizations'
import { useOrganizationsStore } from '@/stores/organizations'

vi.mock('@/api/generated/endpoints/organizations/organizations')

const NAME_INPUT = '.el-dialog input[maxlength="255"]'
const SHORT_NAME_INPUT = '.el-dialog input[maxlength="32"]'

async function mountPage(organizations = createOrganizations()) {
  const { global } = await createTestApp('/admin/organizations')
  useOrganizationsStore().organizations = organizations
  return mount(OrganizationsPage, { global, attachTo: document.body })
}

function findAction(container: DOMWrapper<Element>, text: string) {
  return container.findAll('button').find((button) => button.text() === text)!
}

async function saveDialog() {
  await findButton('Zapisz')!.trigger('click')
  await flushPromises()
}

describe('OrganizationsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.mocked(getOrganizations).mockResolvedValue(createOrganizations())
  })

  it('lists organizations with their suborganizations', async () => {
    const wrapper = await mountPage()

    expect(wrapper.findAll('.organization-header .item-name').map((name) => name.text())).toEqual([
      'Politechnika Wrocławska (PWr)',
      'Uniwersytet Wrocławski (UWr)',
    ])
    expect(wrapper.findAll('.suborganization-item .item-name').map((name) => name.text())).toEqual([
      'Wydział Informatyki',
      'Wydział Mechaniczny',
    ])
    expect(wrapper.text()).toContain('Brak podorganizacji.')
  })

  it('informs that there are no organizations', async () => {
    const wrapper = await mountPage([])

    expect(wrapper.text()).toContain('Brak organizacji.')
  })

  it('adds an organization and reloads the list', async () => {
    const wrapper = await mountPage()
    vi.mocked(getOrganizations).mockResolvedValue([
      { id: 'akademia', name: 'Akademia Sztuk', shortName: 'ASP', suborganizations: [] },
    ])

    await findButton('Dodaj organizację')!.trigger('click')
    await wrapper.find(NAME_INPUT).setValue(' Akademia Sztuk ')
    await wrapper.find(SHORT_NAME_INPUT).setValue(' ASP ')
    await saveDialog()

    expect(addOrganization).toHaveBeenCalledExactlyOnceWith({
      name: 'Akademia Sztuk',
      shortName: 'ASP',
    })
    expect(shownMessages('success')).toEqual(['Zmiany zostały zapisane.'])
    expect(findButton('Zapisz')).toBeUndefined()
    expect(wrapper.find('.organization-header .item-name').text()).toBe('Akademia Sztuk (ASP)')
  })

  it.each([
    ['   ', 'ASP'],
    ['Akademia Sztuk', '  '],
  ])(
    'does not save an organization without the name or the short name',
    async (name, shortName) => {
      const wrapper = await mountPage()

      await findButton('Dodaj organizację')!.trigger('click')
      await wrapper.find(NAME_INPUT).setValue(name)
      await wrapper.find(SHORT_NAME_INPUT).setValue(shortName)

      expect(findButton('Zapisz')!.attributes('disabled')).toBeDefined()
      await wrapper.find('.el-dialog form').trigger('submit')
      expect(addOrganization).not.toHaveBeenCalled()
    },
  )

  it('edits an organization starting from its current data', async () => {
    const wrapper = await mountPage()

    await findAction(wrapper.find('.organization-header'), 'Edytuj').trigger('click')
    expect((wrapper.find(NAME_INPUT).element as HTMLInputElement).value).toBe(
      'Politechnika Wrocławska',
    )
    expect((wrapper.find(SHORT_NAME_INPUT).element as HTMLInputElement).value).toBe('PWr')

    await wrapper.find(SHORT_NAME_INPUT).setValue('PWR')
    await saveDialog()

    expect(updateOrganization).toHaveBeenCalledExactlyOnceWith('pwr', {
      name: 'Politechnika Wrocławska',
      shortName: 'PWR',
    })
    expect(getOrganizations).toHaveBeenCalledOnce()
  })

  it('adds a suborganization to the chosen organization', async () => {
    const wrapper = await mountPage()

    await findAction(wrapper.find('.organization-header'), 'Dodaj podorganizację').trigger('click')
    expect(wrapper.find(SHORT_NAME_INPUT).exists()).toBe(false)
    await wrapper.find(NAME_INPUT).setValue('Wydział Chemiczny')
    await saveDialog()

    expect(addSuborganization).toHaveBeenCalledExactlyOnceWith('pwr', {
      name: 'Wydział Chemiczny',
    })
    expect(shownMessages('success')).toEqual(['Zmiany zostały zapisane.'])
  })

  it('edits a suborganization starting from its current name', async () => {
    const wrapper = await mountPage()

    await findAction(wrapper.findAll('.suborganization-item')[1]!, 'Edytuj').trigger('click')
    expect((wrapper.find(NAME_INPUT).element as HTMLInputElement).value).toBe('Wydział Mechaniczny')

    await wrapper.find(NAME_INPUT).setValue('Wydział Mechaniczno-Energetyczny')
    await saveDialog()

    expect(updateSuborganization).toHaveBeenCalledExactlyOnceWith('pwr', 'w10', {
      name: 'Wydział Mechaniczno-Energetyczny',
    })
  })

  it('opens an empty form for a new organization after editing another one', async () => {
    const wrapper = await mountPage()
    await findAction(wrapper.find('.organization-header'), 'Edytuj').trigger('click')
    await findButton('Anuluj')!.trigger('click')

    await findButton('Dodaj organizację')!.trigger('click')

    expect((wrapper.find(NAME_INPUT).element as HTMLInputElement).value).toBe('')
    expect((wrapper.find(SHORT_NAME_INPUT).element as HTMLInputElement).value).toBe('')
  })

  it('keeps the form open and reports an error when saving fails', async () => {
    vi.mocked(addSuborganization).mockRejectedValue(createHttpError(500))
    const wrapper = await mountPage()

    await findAction(wrapper.find('.organization-header'), 'Dodaj podorganizację').trigger('click')
    await wrapper.find(NAME_INPUT).setValue('Wydział Chemiczny')
    await saveDialog()

    expect(shownMessages('error')).toEqual(['Nie udało się zapisać zmian.'])
    expect(shownMessages('success')).toEqual([])
    expect(findButton('Zapisz')).toBeDefined()
    expect(getOrganizations).not.toHaveBeenCalled()
  })

  it('shows saving as busy until its request ends', async () => {
    const { request, fail } = createFailingRequest()
    vi.mocked(addSuborganization).mockReturnValueOnce(request)
    const wrapper = await mountPage()
    await findAction(wrapper.find('.organization-header'), 'Dodaj podorganizację').trigger('click')
    await wrapper.find(NAME_INPUT).setValue('Wydział Chemiczny')

    await saveDialog()
    expect(findButton('Zapisz')!.classes()).toContain('is-loading')

    fail()
    await flushPromises()
    expect(findButton('Zapisz')!.classes()).not.toContain('is-loading')
  })

  it('deletes an organization after confirmation', async () => {
    const wrapper = await mountPage()
    vi.mocked(getOrganizations).mockResolvedValue(createOrganizations().slice(1))

    await findAction(wrapper.find('.organization-header'), 'Usuń').trigger('click')
    expect(deleteOrganization).not.toHaveBeenCalled()
    await confirmPopconfirm()
    await flushPromises()

    expect(deleteOrganization).toHaveBeenCalledExactlyOnceWith('pwr')
    expect(shownMessages('success')).toEqual(['Organizacja została usunięta.'])
    expect(wrapper.findAll('.organization-header .item-name').map((name) => name.text())).toEqual([
      'Uniwersytet Wrocławski (UWr)',
    ])
  })

  it('reports an organization that could not be deleted', async () => {
    vi.mocked(deleteOrganization).mockRejectedValue(createHttpError(500))
    const wrapper = await mountPage()

    await findAction(wrapper.find('.organization-header'), 'Usuń').trigger('click')
    await confirmPopconfirm()
    await flushPromises()

    expect(shownMessages('error')).toEqual(['Nie udało się usunąć organizacji.'])
    expect(getOrganizations).not.toHaveBeenCalled()
  })

  it('deletes a suborganization after confirmation', async () => {
    const wrapper = await mountPage()

    await findAction(wrapper.findAll('.suborganization-item')[1]!, 'Usuń').trigger('click')
    await confirmPopconfirm()
    await flushPromises()

    expect(deleteSuborganization).toHaveBeenCalledExactlyOnceWith('pwr', 'w10')
    expect(shownMessages('success')).toEqual(['Podorganizacja została usunięta.'])
    expect(getOrganizations).toHaveBeenCalledOnce()
  })

  it('reports a suborganization that could not be deleted', async () => {
    vi.mocked(deleteSuborganization).mockRejectedValue(createHttpError(500))
    const wrapper = await mountPage()

    await findAction(wrapper.find('.suborganization-item'), 'Usuń').trigger('click')
    await confirmPopconfirm()
    await flushPromises()

    expect(shownMessages('error')).toEqual(['Nie udało się usunąć podorganizacji.'])
  })
})
