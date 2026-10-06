import { getCaseApplicationDownloadUrl } from '@/api/generated/endpoints/cases/cases'
import { downloadFromStorage } from '@/utils/storage'

export async function downloadApplicationDocument(applicationId: string): Promise<void> {
  downloadFromStorage(await getCaseApplicationDownloadUrl(applicationId))
}
