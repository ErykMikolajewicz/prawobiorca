import type { ApplicationType } from './applicationType'

export interface NewApplication {
  /** @minLength 1 */
  description: string
  /** @minLength 1 */
  userName: string
  /** @pattern ^\d{6}$ */
  studentId: string
  /** @minLength 1 */
  department: string
  /** @minLength 1 */
  semester: string
  title: string
  applicationType?: ApplicationType
}
