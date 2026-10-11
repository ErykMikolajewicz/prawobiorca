import { describe, it, expect, beforeEach, vi } from 'vitest'

async function importSetPageMeta() {
  vi.resetModules()
  const { setPageMeta } = await import('@/utils/pageMeta')
  return setPageMeta
}

function getDescription() {
  return document.querySelector('meta[name="description"]')?.getAttribute('content')
}

describe('setPageMeta', () => {
  beforeEach(() => {
    document.head.innerHTML = '<meta name="description" content="Default description" />'
    document.title = 'Default title'
  })

  it('sets the given title and description', async () => {
    const setPageMeta = await importSetPageMeta()

    setPageMeta('Page title', 'Page description')

    expect(document.title).toBe('Page title')
    expect(getDescription()).toBe('Page description')
  })

  it('restores the defaults from index.html when no values are given', async () => {
    const setPageMeta = await importSetPageMeta()
    setPageMeta('Page title', 'Page description')

    setPageMeta()

    expect(document.title).toBe('Default title')
    expect(getDescription()).toBe('Default description')
  })
})
