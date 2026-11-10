import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import AppLayout from '../AppLayout.vue'
import { createTestApp } from '@/__tests__/app'
import { page } from '@/__tests__/dom'
import { createOrganizations } from '@/__tests__/factories'
import { getCasesList } from '@/api/generated/endpoints/cases/cases'
import { getOrganizations } from '@/api/generated/endpoints/organizations/organizations'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { useSidebar } from '@/composables/useSidebar'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/api/generated/endpoints/auth/auth')
vi.mock('@/api/generated/endpoints/cases/cases')
vi.mock('@/api/generated/endpoints/organizations/organizations')

async function mountLayout(prepareStores: () => void = () => {}) {
  const { global } = await createTestApp()
  prepareStores()
  const wrapper = mount(AppLayout, {
    slots: { default: '<p class="page-content">Treść strony</p>' },
    global,
    attachTo: document.body,
  })
  await flushPromises()
  return wrapper
}

describe('AppLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useBreakpoint().isMobile.value = false
    useSidebar().isCollapsed.value = false
    vi.mocked(getOrganizations).mockResolvedValue(createOrganizations())
    vi.mocked(getCasesList).mockResolvedValue([{ id: 'case-1', name: 'Urlop dziekański' }])
  })

  it('shows the page between the sidebar and the footer', async () => {
    const wrapper = await mountLayout()

    expect(wrapper.find('main .page-content').text()).toBe('Treść strony')
    expect(wrapper.find('aside .sidebar-content').exists()).toBe(true)
    expect(wrapper.find('footer').text()).toContain('Prawobiorca.')
    expect(wrapper.find('.app-top-bar').exists()).toBe(false)
  })

  it('loads organizations but not cases for a guest', async () => {
    const wrapper = await mountLayout()

    expect(getOrganizations).toHaveBeenCalledOnce()
    expect(getCasesList).not.toHaveBeenCalled()
    expect(wrapper.find('.sidebar-case-item').exists()).toBe(false)
  })

  it('loads the cases of a logged user and selects the first organization', async () => {
    const wrapper = await mountLayout(() => {
      useAuthStore().isUserLogged = true
    })

    expect(getCasesList).toHaveBeenCalledOnce()
    expect(wrapper.find('.sidebar-case-item .case-name').text()).toBe('Urlop dziekański')
    expect(wrapper.find('.context-label').text()).toBe('PWr')
  })

  it('narrows the sidebar when it is collapsed', async () => {
    const wrapper = await mountLayout()
    expect(wrapper.find('aside').attributes('style')).toContain('260px')

    await wrapper.find('button[title="Zwiń menu"]').trigger('click')

    expect(wrapper.find('aside').attributes('style')).toContain('64px')
  })

  it('hides the sidebar on mobile until it is opened from the top bar', async () => {
    useBreakpoint().isMobile.value = true
    const wrapper = await mountLayout()
    expect(wrapper.find('aside').exists()).toBe(false)
    expect(page().find('.sidebar-content').exists()).toBe(false)

    await wrapper.find('.app-top-bar button[title="Rozwiń menu"]').trigger('click')
    await flushPromises()

    expect(page().find('.el-drawer .sidebar-content').exists()).toBe(true)
  })

  it('closes the mobile sidebar from its header', async () => {
    useBreakpoint().isMobile.value = true
    const wrapper = await mountLayout()
    await wrapper.find('.app-top-bar button[title="Rozwiń menu"]').trigger('click')
    await flushPromises()

    await page().find('.el-drawer button[title="Zwiń menu"]').trigger('click')
    await flushPromises()

    expect(useSidebar().isCollapsed.value).toBe(true)
    expect(page().find('.el-drawer').isVisible()).toBe(false)
  })
})
