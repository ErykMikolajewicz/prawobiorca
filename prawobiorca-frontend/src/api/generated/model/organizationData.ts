import type { SuborganizationData } from './suborganizationData'

export interface OrganizationData {
  id: string
  name: string
  shortName: string
  suborganizations: SuborganizationData[]
}
