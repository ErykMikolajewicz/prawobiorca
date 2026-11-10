import { describe, it, expect, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import PinnedDocumentsList from '../PinnedDocumentsList.vue'
import { findButton, page } from '@/__tests__/dom'
import { createCaseDocument } from '@/__tests__/factories'
import type { CaseDocument } from '@/api/generated/model'

const firstDocument = createCaseDocument({
  id: 'document-1',
  presentationName: 'Regulamin studiów',
  header: '§ 12',
  elements: [
    { text: '1. Student ma prawo do urlopu.', subsection: '1' },
    { text: '2. Urlopu udziela dziekan.', subsection: '2' },
  ],
  highlight: { start_element: 1, end_element: 1 },
})
const secondDocument = createCaseDocument({
  id: 'document-2',
  presentationName: 'Statut',
  header: null,
  content: 'Treść dokumentu bez podziału.',
  elements: [],
})

function mountList(
  documents: Array<CaseDocument> = [firstDocument, secondDocument],
  stubs: Record<string, boolean> = {},
) {
  return mount(PinnedDocumentsList, {
    props: { documents },
    global: { plugins: [ElementPlus], stubs },
    attachTo: document.body,
  })
}

function isDrawerOpen() {
  const drawer = page().find('.el-drawer')
  return drawer.exists() && drawer.isVisible()
}

describe('PinnedDocumentsList', () => {
  it('lists pinned documents with the regulation name and the article', () => {
    const wrapper = mountList()

    expect(wrapper.findAll('.pinned-document').map((card) => card.text())).toEqual([
      'Regulamin studiów§ 12',
      'Statut',
    ])
    expect(isDrawerOpen()).toBe(false)
  })

  it('informs that nothing is pinned', () => {
    const wrapper = mountList([])

    expect(wrapper.text()).toContain('Brak przypiętych artykułów do tej sprawy.')
  })

  it('shows the clicked document with its highlighted fragment', async () => {
    const wrapper = mountList()

    await wrapper.find('.pinned-document').trigger('click')

    const drawer = page().find('.el-drawer')
    expect(drawer.find('.drawer-header em').text()).toBe('Regulamin studiów')
    expect(drawer.find('h3').text()).toBe('§ 12')
    expect(drawer.findAll('.result-block').map((block) => block.text())).toEqual([
      '1. Student ma prawo do urlopu.',
      '2. Urlopu udziela dziekan.',
    ])
    expect(drawer.find('.result-block.is-highlighted').text()).toBe('2. Urlopu udziela dziekan.')
  })

  it('shows a document without an article under the regulation name with its plain content', async () => {
    const wrapper = mountList()

    await wrapper.findAll('.pinned-document')[1]!.trigger('keydown', { key: 'Enter' })

    const drawer = page().find('.el-drawer')
    expect(drawer.find('.drawer-header em').exists()).toBe(false)
    expect(drawer.find('h3').text()).toBe('Statut')
    expect(drawer.find('.content').text()).toBe('Treść dokumentu bez podziału.')
    expect(drawer.find('.result-block').exists()).toBe(false)
  })

  it('unpins a document from its card without opening it', async () => {
    const wrapper = mountList()

    await wrapper.find('.pinned-document button[aria-label="Odepnij"]').trigger('click')

    expect(wrapper.emitted('unpin')).toEqual([['document-1']])
    expect(isDrawerOpen()).toBe(false)
  })

  it('unpins the shown document and closes it', async () => {
    const wrapper = mountList()
    await wrapper.findAll('.pinned-document')[1]!.trigger('click')

    await findButton('Odepnij')!.trigger('click')
    await flushPromises()

    expect(wrapper.emitted('unpin')).toEqual([['document-2']])
    expect(isDrawerOpen()).toBe(false)
  })

  it('keeps the shown document open when another one is unpinned', async () => {
    const wrapper = mountList()
    await wrapper.findAll('.pinned-document')[1]!.trigger('click')

    await wrapper.find('.pinned-document button[aria-label="Odepnij"]').trigger('click')
    await flushPromises()

    expect(wrapper.emitted('unpin')).toEqual([['document-1']])
    expect(isDrawerOpen()).toBe(true)
  })

  it('closes the shown document and shows it again when clicked', async () => {
    const wrapper = mountList(undefined, { transition: false })
    await wrapper.find('.pinned-document').trigger('click')
    await vi.waitFor(() => expect(isDrawerOpen()).toBe(true))

    await page().find('.el-drawer__close-btn').trigger('click')
    await vi.waitFor(() => expect(isDrawerOpen()).toBe(false))

    await wrapper.find('.pinned-document').trigger('click')
    await vi.waitFor(() => expect(isDrawerOpen()).toBe(true))
  })

  it('closes the shown document when it is no longer pinned', async () => {
    const wrapper = mountList()
    await wrapper.find('.pinned-document').trigger('click')

    await wrapper.setProps({ documents: [secondDocument] })
    await flushPromises()

    expect(isDrawerOpen()).toBe(false)
  })
})
