import { describe, it, expect } from 'vitest'
import { defineComponent, h } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory, useRoute } from 'vue-router'
import App from '../App.vue'

let createdPages = 0

const CasePage = defineComponent({
  setup() {
    createdPages++
    const caseId = useRoute().params.id as string
    return () => h('div', `Sprawa ${caseId}`)
  },
})

async function mountApp(path: string) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/cases/:id', component: CasePage }],
  })
  await router.push(path)
  const wrapper = mount(App, { global: { plugins: [router] } })
  return { router, wrapper }
}

describe('App', () => {
  it('shows the page of the current route', async () => {
    const { wrapper } = await mountApp('/cases/1')

    expect(wrapper.text()).toBe('Sprawa 1')
  })

  it('creates the page again when only a route parameter changes', async () => {
    const { router, wrapper } = await mountApp('/cases/1')

    await router.push('/cases/2')
    await flushPromises()

    expect(wrapper.text()).toBe('Sprawa 2')
  })

  it('keeps the page when only the query changes', async () => {
    createdPages = 0
    const { router } = await mountApp('/cases/1')

    await router.push('/cases/1?query=urlop')
    await flushPromises()

    expect(createdPages).toBe(1)
  })
})
