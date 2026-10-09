import type { PublishedApplicationField } from './publishedApplicationField'

export interface PublishedApplicationTemplate {
  id: string
  name: string
  fields: PublishedApplicationField[]
}
