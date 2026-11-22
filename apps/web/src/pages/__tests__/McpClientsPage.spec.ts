import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import McpClientsPage from '../McpClientsPage.vue'
import { createTestApp } from '@/__tests__/app'
import { confirmPopconfirm, findButton, shownMessages } from '@/__tests__/dom'
import { createHttpError } from '@/__tests__/factories'
import {
  createOauthClient,
  deleteOauthClient,
  getOauthClients,
} from '@/api/generated/endpoints/oauth-clients/oauth-clients'

import type { OAuthClientData } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/oauth-clients/oauth-clients')

const NAME_INPUT = '.el-dialog input[maxlength="100"]'

const CLIENTS: Array<OAuthClientData> = [
  { id: 'client-1', name: 'Claude', createDate: '2026-11-22T10:00:00Z' },
]

async function mountPage() {
  const { global } = await createTestApp('/admin/mcp-clients')
  const wrapper = mount(McpClientsPage, { global, attachTo: document.body })
  await flushPromises()
  return wrapper
}

function shownInputValues(wrapper: Awaited<ReturnType<typeof mountPage>>) {
  return wrapper
    .findAll('.created-client input')
    .map((input) => (input.element as HTMLInputElement).value)
}

describe('McpClientsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.mocked(getOauthClients).mockResolvedValue([...CLIENTS])
  })

  it('lists MCP clients', async () => {
    const wrapper = await mountPage()

    expect(wrapper.find('.el-table').text()).toContain('Claude')
  })

  it('creates a client and shows its secret once', async () => {
    vi.mocked(createOauthClient).mockResolvedValue({ id: 'client-2', secret: 'top-secret' })
    const wrapper = await mountPage()

    await findButton('Dodaj klienta')!.trigger('click')
    await wrapper.find(NAME_INPUT).setValue(' Claude Code ')
    await findButton('Zapisz')!.trigger('click')
    await flushPromises()

    expect(createOauthClient).toHaveBeenCalledExactlyOnceWith({ name: 'Claude Code' })
    expect(getOauthClients).toHaveBeenCalledTimes(2)
    expect(wrapper.get('.server-address dd').text()).toBe(`${window.location.origin}/api/mcp`)
    expect(shownInputValues(wrapper)).toEqual(['client-2', 'top-secret'])

    await findButton('Gotowe')!.trigger('click')

    expect(wrapper.find('.created-client').exists()).toBe(false)
  })

  it('does not create a client without a name', async () => {
    const wrapper = await mountPage()

    await findButton('Dodaj klienta')!.trigger('click')
    await wrapper.find(NAME_INPUT).setValue('   ')

    expect(findButton('Zapisz')!.attributes('disabled')).toBeDefined()
    await wrapper.find('.el-dialog form').trigger('submit')
    expect(createOauthClient).not.toHaveBeenCalled()
  })

  it('deletes a client after confirmation', async () => {
    const wrapper = await mountPage()

    await wrapper.find('.el-table .el-button--danger').trigger('click')
    await confirmPopconfirm()
    await flushPromises()

    expect(deleteOauthClient).toHaveBeenCalledExactlyOnceWith('client-1')
    expect(shownMessages('success')).toEqual(['Klient MCP został usunięty.'])
  })

  it('informs when clients can not be loaded', async () => {
    vi.mocked(getOauthClients).mockRejectedValue(createHttpError(500))

    await mountPage()

    expect(shownMessages('error')).toEqual(['Nie udało się pobrać klientów MCP.'])
  })
})
