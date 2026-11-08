const descriptionElement = document.querySelector<HTMLMetaElement>('meta[name="description"]')
const defaultTitle = document.title
const defaultDescription = descriptionElement?.content ?? ''

export function setPageMeta(title?: string, description?: string): void {
  document.title = title ?? defaultTitle
  descriptionElement?.setAttribute('content', description ?? defaultDescription)
}
