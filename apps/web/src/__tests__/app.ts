import ElementPlus from 'element-plus'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter, type RouteRecordRaw } from 'vue-router'
import appRouter from '@/router'

const EmptyPage = { render: () => null }
const LayoutStub = { template: '<div><slot /></div>' }

function withoutPage(route: RouteRecordRaw): RouteRecordRaw {
  return route.component ? { ...route, component: EmptyPage } : route
}

export async function createTestApp(path = '/') {
  const pinia = createPinia()
  setActivePinia(pinia)

  const router = createRouter({
    history: createMemoryHistory(),
    routes: appRouter.options.routes.map(withoutPage),
  })
  await router.push(path)

  return {
    router,
    global: { plugins: [ElementPlus, pinia, router], stubs: { AppLayout: LayoutStub } },
  }
}
