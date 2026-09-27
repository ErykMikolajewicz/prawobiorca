import axios from 'axios'

import * as regulationsApi from '@/api/generated/endpoints/regulations/regulations'
import * as userRegulationsApi from '@/api/generated/endpoints/user-regulations/user-regulations'
import type { RegulationUploadTarget } from '@/api/generated/model'

export function toBrowserStorageUrl(url: string): string {
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

export async function getPublicRegulationDownloadUrl(regulationId: string): Promise<string> {
  const url = await regulationsApi.getPublicRegulationDownloadUrl(regulationId)
  return toBrowserStorageUrl(url)
}

export async function getUserRegulationDownloadUrl(regulationId: string): Promise<string> {
  const url = await userRegulationsApi.getUserRegulationDownloadUrl(regulationId)
  return toBrowserStorageUrl(url)
}
