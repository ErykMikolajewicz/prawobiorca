import { getAdminApplicationTemplateDownloadUrl } from '@/api/generated/endpoints/application-templates/application-templates'
import { downloadFromStorage } from '@/utils/storage'

export async function downloadApplicationTemplate(templateId: string): Promise<void> {
  downloadFromStorage(await getAdminApplicationTemplateDownloadUrl(templateId))
}
