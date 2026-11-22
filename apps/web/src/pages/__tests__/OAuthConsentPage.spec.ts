import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import OAuthConsentPage from '../OAuthConsentPage.vue'
import { createTestApp } from '@/__tests__/app'
import { findButton } from '@/__tests__/dom'
import { createHttpError } from '@/__tests__/factories'
import { getConsentDetails, grantConsent } from '@/api/generated/endpoints/oauth/oauth'

vi.mock('@/api/generated/endpoints/oauth/oauth')

const AUTHORIZATION_REQUEST = {
  clientId: 'client-1',
  redirectUri: 'https://claude.ai/api/mcp/auth_callback',
  resource: 'https://www.prawobiorca.pl/api/mcp',
  codeChallenge: 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM',
  state: 'client-state',
}

async function mountPage() {
  const query = new URLSearchParams(AUTHORIZATION_REQUEST).toString()
  const { global } = await createTestApp(`/oauth/consent?${query}`)
  const wrapper = mount(OAuthConsentPage, { global, attachTo: document.body })
  await flushPromises()
  return wrapper
}

describe('OAuthConsentPage', () => {
  const assign = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.stubGlobal('location', { assign })
    vi.mocked(getConsentDetails).mockResolvedValue({ clientName: 'Claude' })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('asks for consent on behalf of the client', async () => {
    const wrapper = await mountPage()

    expect(getConsentDetails).toHaveBeenCalledExactlyOnceWith(AUTHORIZATION_REQUEST)
    expect(wrapper.text()).toContain('Aplikacja Claude prosi o dostęp')
  })

  it('redirects to the client with the authorization code after granting access', async () => {
    vi.mocked(grantConsent).mockResolvedValue({
      redirectUrl: 'https://claude.ai/api/mcp/auth_callback?code=abc&state=client-state',
    })
    await mountPage()

    await findButton('Zezwól')!.trigger('click')
    await flushPromises()

    expect(grantConsent).toHaveBeenCalledExactlyOnceWith(AUTHORIZATION_REQUEST)
    expect(assign).toHaveBeenCalledExactlyOnceWith(
      'https://claude.ai/api/mcp/auth_callback?code=abc&state=client-state',
    )
  })

  it('redirects to the client with an error after denying access', async () => {
    await mountPage()

    await findButton('Odmów')!.trigger('click')

    expect(grantConsent).not.toHaveBeenCalled()
    expect(assign).toHaveBeenCalledExactlyOnceWith(
      'https://claude.ai/api/mcp/auth_callback?error=access_denied&state=client-state',
    )
  })

  it('informs about an invalid authorization request', async () => {
    vi.mocked(getConsentDetails).mockRejectedValue(createHttpError(400))
    const wrapper = await mountPage()

    expect(wrapper.text()).toContain('Nieprawidłowa prośba o dostęp')
    expect(findButton('Zezwól')).toBeUndefined()
  })
})
