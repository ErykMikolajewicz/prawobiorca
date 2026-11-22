export interface AuthorizationRequest {
  clientId: string
  /**
   * @minLength 1
   * @maxLength 2000
   */
  redirectUri: string
  resource: string
  /** @pattern ^[A-Za-z0-9\-._~]{43,128}$ */
  codeChallenge: string
  state?: string | null
}
