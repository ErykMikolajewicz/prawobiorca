import {
  generateApplication,
  getCaseApplicationDownloadUrl,
} from '@/api/generated/endpoints/cases/cases'
import type { NewApplication } from '@/api/generated/model'
import { toBrowserStorageUrl } from '@/utils/storage'

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

export async function downloadApplicationDocument(applicationId: string): Promise<void> {
  const url = toBrowserStorageUrl(await getCaseApplicationDownloadUrl(applicationId))

  const link = document.createElement('a')
  link.href = url
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
