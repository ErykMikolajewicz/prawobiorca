export interface LoginData {
  username: string
  /**
   * @minLength 8
   * @maxLength 32
   */
  password: string
}
