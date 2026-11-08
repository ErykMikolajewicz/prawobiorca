import type { NewApplicationFieldValues } from './newApplicationFieldValues'

export interface NewApplication {
  templateId: string
  /** @minLength 1 */
  description: string
  fieldValues?: NewApplicationFieldValues
}
