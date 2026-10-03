let handler: (() => void) | null = null

/**
 * Odrzucenie żądania po trwałej utracie sesji. Użytkownika informuje już handler,
 * więc wywołujący nie powinien pokazywać własnego komunikatu.
 */
export class SessionExpiredError extends Error {}

/**
 * Rejestruje reakcję na trwałą utratę sesji (nieudane odświeżenie tokenów).
 * Wołane z main.ts, żeby warstwa API nie zależała od store'a ani routera.
 */
export function setSessionExpiredHandler(fn: (() => void) | null): void {
  handler = fn
}

export function notifySessionExpired(): void {
  handler?.()
}
