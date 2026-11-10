import { afterEach } from 'vitest'
import { enableAutoUnmount } from '@vue/test-utils'

afterEach(() => {
  document.body.replaceChildren()
  localStorage.clear()
})

enableAutoUnmount(afterEach)
