import { getCaseApplicationDownloadUrl } from '@/api/generated/endpoints/cases/cases'
import { toBrowserStorageUrl } from '@/utils/storage'

export async function downloadApplicationDocument(applicationId: string): Promise<void> {
  const url = toBrowserStorageUrl(await getCaseApplicationDownloadUrl(applicationId))

  const link = document.createElement('a')
  link.href = url
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
