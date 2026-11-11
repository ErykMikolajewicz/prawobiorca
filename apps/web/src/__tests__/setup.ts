import { deepStrictEqual } from 'node:assert'
import { afterEach, beforeEach } from 'vitest'
import { config, enableAutoUnmount, flushPromises } from '@vue/test-utils'

let componentErrors: Array<unknown> | undefined

config.global.config.errorHandler = (error) => {
  if (!componentErrors) throw error
  componentErrors.push(error)
}

beforeEach(() => {
  componentErrors = []
})

afterEach(async () => {
  await flushPromises()
  document.body.replaceChildren()
  localStorage.clear()
  const errors = componentErrors
  componentErrors = undefined
  deepStrictEqual(errors, [], 'Unhandled Vue component errors')
})

enableAutoUnmount(afterEach)
