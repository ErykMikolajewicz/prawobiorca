export interface RegistrationData {
  username: string
  /**
   * @minLength 8
   * @maxLength 32
   */
  password: string
}
