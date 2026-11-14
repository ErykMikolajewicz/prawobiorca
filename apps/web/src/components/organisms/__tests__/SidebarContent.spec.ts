import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import SidebarContent from '../SidebarContent.vue'
import { createTestApp } from '@/__tests__/app'
import { confirmPopconfirm, findButton, findOption, page, shownMessages } from '@/__tests__/dom'
import { createFailingRequest, createHttpError, createOrganizations } from '@/__tests__/factories'
import { logoutUser } from '@/api/generated/endpoints/auth/auth'
import { addCase, deleteUserCase } from '@/api/generated/endpoints/cases/cases'
import { useDarkMode } from '@/composables/useDarkMode'
import { useSidebar } from '@/composables/useSidebar'
import { useAuthStore } from '@/stores/auth'
import { useCasesStore } from '@/stores/cases'
import { useOrganizationsStore } from '@/stores/organizations'

vi.mock('@/api/generated/endpoints/auth/auth')
vi.mock('@/api/generated/endpoints/cases/cases')

function logIn(isAdmin = false) {
  const authStore = useAuthStore()
  authStore.isUserLogged = true
  authStore.isAdmin = isAdmin
}

function logInWithCases() {
  logIn()
  const casesStore = useCasesStore()
  casesStore.cases = [
    { id: 'case-1', name: 'Urlop dziekański' },
    { id: 'case-2', name: 'Stypendium' },
  ]
  casesStore.setActive('case-1')
}

function withOrganizations() {
  useOrganizationsStore().organizations = createOrganizations()
}

async function mountSidebar(prepareStores: () => void = () => {}, path = '/') {
  const { router, global } = await createTestApp(path)
  prepareStores()
  const wrapper = mount(SidebarContent, { global, attachTo: document.body })
  return { router, wrapper }
}

function caseNames(wrapper: VueWrapper) {
  return wrapper.findAll('.sidebar-case-item .case-name').map((name) => name.text())
}

async function createCase(wrapper: VueWrapper, name: string) {
  await wrapper.find('input[placeholder="Nowa sprawa..."]').setValue(name)
  await wrapper.find('form.case-form').trigger('submit')
  await flushPromises()
}

async function openContextMenu(wrapper: VueWrapper) {
  await wrapper.find('.context-trigger').trigger('click')
  await vi.waitUntil(() => {
    const menu = page().find('.context-menu')
    return menu.exists() && menu.isVisible()
  })
}

describe('SidebarContent', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    useSidebar().isCollapsed.value = false
    useDarkMode().isDark.value = false
  })

  describe('navigation', () => {
    it('shows a guest only the main page link', async () => {
      const { wrapper } = await mountSidebar()

      expect(wrapper.findAll('.el-menu-item').map((item) => item.text())).toEqual(['Strona główna'])
      expect(wrapper.text()).not.toContain('Administracja')
      expect(wrapper.text()).not.toContain('Moje sprawy')
    })

    it('does not show the administration menu to a regular user', async () => {
      const { wrapper } = await mountSidebar(logIn)

      expect(wrapper.text()).not.toContain('Administracja')
    })

    it.each([
      ['Szablony wniosków', '/admin/application-templates'],
      ['Organizacje', '/admin/organizations'],
      ['Strona główna', '/'],
    ])('opens "%s" from the menu of an administrator', async (label, path) => {
      const { router, wrapper } = await mountSidebar(() => logIn(true), '/features')

      await wrapper
        .findAll('.el-menu-item')
        .find((item) => item.text() === label)!
        .trigger('click')
      await flushPromises()

      expect(router.currentRoute.value.path).toBe(path)
    })

    it('collapses to icons and expands back', async () => {
      const { wrapper } = await mountSidebar(logInWithCases)
      expect(wrapper.find('.logo').exists()).toBe(true)

      await wrapper.find('button[title="Zwiń menu"]').trigger('click')
      expect(wrapper.find('.logo').exists()).toBe(false)
      expect(wrapper.find('.sidebar-case-item').exists()).toBe(false)

      await wrapper.find('button[title="Moje sprawy"]').trigger('click')
      expect(wrapper.find('.logo').exists()).toBe(true)
      expect(caseNames(wrapper)).toEqual(['Urlop dziekański', 'Stypendium'])
    })
  })

  describe('cases', () => {
    it('lists cases with links to them and marks the active one', async () => {
      const { wrapper } = await mountSidebar(logInWithCases)

      expect(caseNames(wrapper)).toEqual(['Urlop dziekański', 'Stypendium'])
      expect(wrapper.find('.sidebar-case-item a').attributes('href')).toBe('/user/cases/case-1')
      expect(
        wrapper
          .findAll('button[aria-label="Ustaw jako aktywną sprawę"]')
          .map((button) => button.classes('is-active')),
      ).toEqual([true, false])
    })

    it('creates a case, puts it first and makes it active', async () => {
      vi.mocked(addCase).mockResolvedValue('case-3')
      const { wrapper } = await mountSidebar(logInWithCases)

      await createCase(wrapper, '  Przepisanie oceny ')

      expect(addCase).toHaveBeenCalledExactlyOnceWith({ caseName: 'Przepisanie oceny' })
      expect(caseNames(wrapper)).toEqual(['Przepisanie oceny', 'Urlop dziekański', 'Stypendium'])
      expect(useCasesStore().activeCase).toEqual({ id: 'case-3', name: 'Przepisanie oceny' })
      expect(
        wrapper.find<HTMLInputElement>('input[placeholder="Nowa sprawa..."]').element.value,
      ).toBe('')
    })

    it('does not create a case without a name', async () => {
      const { wrapper } = await mountSidebar(logInWithCases)

      await createCase(wrapper, '   ')

      expect(addCase).not.toHaveBeenCalled()
    })

    it('limits the case name to the length accepted by the API', async () => {
      const { wrapper } = await mountSidebar(logInWithCases)

      expect(wrapper.find('input[placeholder="Nowa sprawa..."]').attributes('maxlength')).toBe(
        '255',
      )
    })

    it('does not create the same case twice when submitted again before the first ends', async () => {
      let finishCreation: ((caseId: string) => void) | undefined
      vi.mocked(addCase).mockImplementationOnce(
        () => new Promise((resolve) => (finishCreation = resolve)),
      )
      const { wrapper } = await mountSidebar(logInWithCases)

      await createCase(wrapper, 'Przepisanie oceny')
      expect(
        wrapper.find('button[aria-label="Utwórz sprawę"]').attributes('disabled'),
      ).toBeDefined()
      await wrapper.find('form.case-form').trigger('submit')
      finishCreation?.('case-3')
      await flushPromises()

      expect(addCase).toHaveBeenCalledOnce()
      expect(
        wrapper.find('button[aria-label="Utwórz sprawę"]').attributes('disabled'),
      ).toBeUndefined()
    })

    it('keeps the typed name and reports an error when the case cannot be created', async () => {
      vi.mocked(addCase).mockRejectedValue(createHttpError(500))
      const { wrapper } = await mountSidebar(logInWithCases)

      await createCase(wrapper, 'Przepisanie oceny')

      expect(shownMessages('error')).toEqual(['Nie udało się utworzyć sprawy.'])
      expect(caseNames(wrapper)).toEqual(['Urlop dziekański', 'Stypendium'])
      expect(
        wrapper.find<HTMLInputElement>('input[placeholder="Nowa sprawa..."]').element.value,
      ).toBe('Przepisanie oceny')
    })

    it('sets another case as active', async () => {
      const { wrapper } = await mountSidebar(logInWithCases)

      await wrapper.findAll('button[aria-label="Ustaw jako aktywną sprawę"]')[1]!.trigger('click')

      expect(useCasesStore().activeCaseId).toBe('case-2')
      expect(
        wrapper
          .findAll('button[aria-label="Ustaw jako aktywną sprawę"]')
          .map((button) => button.classes('is-active')),
      ).toEqual([false, true])
    })

    it('deletes a case after confirmation and stays on the current page', async () => {
      const { router, wrapper } = await mountSidebar(logInWithCases, '/user/cases/case-2')

      await wrapper.find('button[aria-label="Usuń sprawę"]').trigger('click')
      expect(deleteUserCase).not.toHaveBeenCalled()
      await confirmPopconfirm()
      await flushPromises()

      expect(deleteUserCase).toHaveBeenCalledExactlyOnceWith('case-1')
      expect(shownMessages('success')).toEqual(['Sprawa została usunięta'])
      expect(caseNames(wrapper)).toEqual(['Stypendium'])
      expect(useCasesStore().activeCaseId).toBe('case-2')
      expect(router.currentRoute.value.fullPath).toBe('/user/cases/case-2')
    })

    it('opens the main page after deleting the case being viewed', async () => {
      const { router, wrapper } = await mountSidebar(logInWithCases, '/user/cases/case-1')

      await wrapper.find('button[aria-label="Usuń sprawę"]').trigger('click')
      await confirmPopconfirm()
      await flushPromises()

      expect(router.currentRoute.value.name).toBe('MainPage')
    })

    it('blocks deleting a case again until the first request ends', async () => {
      const { request, fail } = createFailingRequest()
      vi.mocked(deleteUserCase).mockReturnValueOnce(request)
      const { wrapper } = await mountSidebar(logInWithCases)
      const deleteButton = wrapper.find('button[aria-label="Usuń sprawę"]')

      await deleteButton.trigger('click')
      await confirmPopconfirm()
      await flushPromises()
      expect(deleteButton.attributes('disabled')).toBeDefined()

      fail()
      await flushPromises()
      expect(deleteButton.attributes('disabled')).toBeUndefined()
    })

    it('keeps the case and reports an error when deleting fails', async () => {
      vi.mocked(deleteUserCase).mockRejectedValue(createHttpError(500))
      const { router, wrapper } = await mountSidebar(logInWithCases, '/user/cases/case-1')

      await wrapper.find('button[aria-label="Usuń sprawę"]').trigger('click')
      await confirmPopconfirm()
      await flushPromises()

      expect(shownMessages('error')).toEqual(['Nie udało się usunąć sprawy'])
      expect(caseNames(wrapper)).toEqual(['Urlop dziekański', 'Stypendium'])
      expect(router.currentRoute.value.name).toBe('CasePage')
    })
  })

  describe('context menu', () => {
    it('asks to choose an organization when none is selected', async () => {
      const { wrapper } = await mountSidebar(withOrganizations)

      expect(wrapper.find('.context-trigger').text()).toBe('Wybierz organizację')
    })

    it('allows choosing a suborganization only of an organization that has them', async () => {
      const { wrapper } = await mountSidebar(withOrganizations)
      await openContextMenu(wrapper)
      const suborganizationSelect = page().findAll('.context-menu .el-select__wrapper')[1]!
      expect(suborganizationSelect.classes()).toContain('is-disabled')

      await findOption('Politechnika Wrocławska')!.trigger('click')
      expect(suborganizationSelect.classes()).not.toContain('is-disabled')

      await findOption('Uniwersytet Wrocławski')!.trigger('click')
      expect(suborganizationSelect.classes()).toContain('is-disabled')
    })

    it('shows the selected organization and suborganization', async () => {
      const { wrapper } = await mountSidebar(() => {
        withOrganizations()
        useOrganizationsStore().select('pwr', 'w10')
      })

      expect(wrapper.find('.context-label').text()).toBe('PWr')
      expect(wrapper.find('.context-trigger').text()).toContain('Wydział Mechaniczny')
      expect(wrapper.find('.context-trigger').attributes('title')).toBe('PWr · Wydział Mechaniczny')
    })

    it('changes the organization context and forgets the suborganization of the previous one', async () => {
      const { wrapper } = await mountSidebar(withOrganizations)
      const organizationsStore = useOrganizationsStore()
      await openContextMenu(wrapper)

      await findOption('Politechnika Wrocławska')!.trigger('click')
      await findOption('Wydział Informatyki')!.trigger('click')
      expect(organizationsStore.selectedOrganizationId).toBe('pwr')
      expect(organizationsStore.selectedSuborganizationId).toBe('w4')

      await findOption('Uniwersytet Wrocławski')!.trigger('click')
      expect(organizationsStore.selectedOrganizationId).toBe('uwr')
      expect(organizationsStore.selectedSuborganizationId).toBe('')
      expect(wrapper.find('.context-label').text()).toBe('UWr')
    })

    it('switches between the light and the dark theme', async () => {
      const { wrapper } = await mountSidebar()
      await openContextMenu(wrapper)

      await page().find('button[title="Przełącz na tryb ciemny"]').trigger('click')

      expect(useDarkMode().isDark.value).toBe(true)
      expect(page().find('button[title="Przełącz na tryb jasny"]').exists()).toBe(true)
    })

    it('opens the login page for a guest', async () => {
      const { router, wrapper } = await mountSidebar()
      await openContextMenu(wrapper)

      await findButton('Zaloguj się')!.trigger('click')
      await flushPromises()

      expect(findButton('Wyloguj się')).toBeUndefined()
      expect(router.currentRoute.value.name).toBe('LoginPage')
    })

    it('logs the user out and opens the main page', async () => {
      const { router, wrapper } = await mountSidebar(logInWithCases, '/user/cases/case-1')
      await openContextMenu(wrapper)

      await findButton('Wyloguj się')!.trigger('click')
      await flushPromises()

      expect(logoutUser).toHaveBeenCalledOnce()
      expect(useAuthStore().isUserLogged).toBe(false)
      expect(router.currentRoute.value.name).toBe('MainPage')
      expect(wrapper.text()).not.toContain('Moje sprawy')
    })

    it('ends the session in the browser even when logging out fails', async () => {
      vi.mocked(logoutUser).mockRejectedValue(createHttpError(500))
      const { router, wrapper } = await mountSidebar(logInWithCases, '/user/cases/case-1')
      await openContextMenu(wrapper)

      await findButton('Wyloguj się')!.trigger('click')
      await flushPromises()

      expect(shownMessages('error')).toEqual(['Nie udało się wylogować.'])
      expect(useAuthStore().isUserLogged).toBe(false)
      expect(router.currentRoute.value.name).toBe('MainPage')
    })
  })
})
