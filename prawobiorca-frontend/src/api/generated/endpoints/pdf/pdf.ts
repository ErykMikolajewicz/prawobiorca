import type { GenerateCasePDFRequest } from '../../model'

import { prawobiorcaRequest } from '../../../axios'

type SecondParameter<T extends (...args: never) => unknown> = Parameters<T>[1]

/**
 * @summary Generate Case Pdf
 */
export const generateCasePdf = (
  generateCasePDFRequest: GenerateCasePDFRequest,
  options?: SecondParameter<typeof prawobiorcaRequest<unknown>>,
) => {
  return prawobiorcaRequest<unknown>(
    {
      url: `/api/case/generate-pdf`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      data: generateCasePDFRequest,
    },
    options,
  )
}
export type GenerateCasePdfResult = NonNullable<Awaited<ReturnType<typeof generateCasePdf>>>
