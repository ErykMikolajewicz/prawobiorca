import { generateApplication } from '@/api/generated/endpoints/cases/cases'
import type { NewApplication } from '@/api/generated/model'

export async function generateApplicationDocument(
  caseId: string,
  newApplication: NewApplication,
): Promise<void> {
  const file = await generateApplication(caseId, newApplication)

  const url = window.URL.createObjectURL(file)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `wniosek_${caseId}.docx`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
