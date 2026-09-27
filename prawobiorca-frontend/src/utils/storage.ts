import axios from 'axios'

import type { RegulationUploadTarget } from '@/api/generated/model'

function toBrowserStorageUrl(url: string): string {
  if (import.meta.env.DEV && url.includes('localhost:9000')) {
    return url.replace(/^https?:\/\/localhost:9000/, '/storage')
  }
  return url
}

export async function uploadFileToStorage(
  target: RegulationUploadTarget,
  file: File,
): Promise<void> {
  const formData = new FormData()
  for (const [key, value] of Object.entries(target.fields)) {
    formData.append(key, value)
  }
  formData.append('file', file)

  await axios.post(toBrowserStorageUrl(target.url), formData)
}
