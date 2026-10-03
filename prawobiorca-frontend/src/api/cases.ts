import { generateApplication } from '@/api/generated/endpoints/cases/cases'
import type { NewApplication } from '@/api/generated/model'

export async function generatePdf(caseId: string, newApplication: NewApplication): Promise<void> {
  const pdf = await generateApplication(caseId, newApplication)

  const url = window.URL.createObjectURL(pdf)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `wniosek_${caseId}.pdf`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
