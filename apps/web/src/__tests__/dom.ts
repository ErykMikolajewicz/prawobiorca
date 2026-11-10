import { vi } from 'vitest'
import { DOMWrapper } from '@vue/test-utils'

type MessageType = 'success' | 'warning' | 'error'

export function page(): DOMWrapper<HTMLElement> {
  return new DOMWrapper(document.body)
}

export function findButton(text: string): DOMWrapper<HTMLButtonElement> | undefined {
  return page()
    .findAll<HTMLButtonElement>('button')
    .find((button) => button.text() === text && button.isVisible())
}

export function findOption(label: string): DOMWrapper<HTMLElement> | undefined {
  return page()
    .findAll<HTMLElement>('.el-select-dropdown__item')
    .find((option) => option.text() === label)
}

export async function confirmPopconfirm(): Promise<void> {
  const confirmButton = await vi.waitUntil(() => findButton('Tak'), { timeout: 5000 })
  await confirmButton.trigger('click')
}

export function shownMessages(type: MessageType): Array<string> {
  return page()
    .findAll(`.el-message--${type}`)
    .map((message) => message.text())
}

export function mockLinkClicks(): Array<string> {
  const clickedUrls: Array<string> = []
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
    this: HTMLAnchorElement,
  ) {
    clickedUrls.push(this.getAttribute('href') ?? '')
  })
  return clickedUrls
}
