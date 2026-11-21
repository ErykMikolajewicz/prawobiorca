export interface UsageTariffData {
  /** @minimum 0 */
  semanticSearchPrice: number
  /** @minimum 0 */
  applicationGenerationPrice: number
  /** @minimum 0 */
  regulationPreparationPrice: number
  /** @minimum 0 */
  accountDailyLimit: number
  /** @minimum 0 */
  anonymousIpDailyLimit: number
  /** @minimum 0 */
  anonymousTotalDailyLimit: number
}
