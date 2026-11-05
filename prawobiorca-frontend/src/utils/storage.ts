import axios from 'axios'

import type { RegulationUploadTarget } from '@/api/generated/model'

const UPLOAD_TIMEOUT_MS = 300_000

export function toBrowserStorageUrl(url: string): string {
  const devStorageOrigin = import.meta.env.VITE_DEV_STORAGE_ORIGIN
  if (devStorageOrigin && url.startsWith(devStorageOrigin)) {
    return '/storage' + url.slice(devStorageOrigin.length)
  }
  return url
}

export async function uploadFileToStorage(
  target: RegulationUploadTarget,
  file: File,
  signal?: AbortSignal,
): Promise<void> {
  const formData = new FormData()
  for (const [key, value] of Object.entries(target.fields)) {
    formData.append(key, value)
  }
  formData.append('file', file)

  await axios.post(toBrowserStorageUrl(target.url), formData, {
    timeout: UPLOAD_TIMEOUT_MS,
    signal,
  })
}

export function downloadFromStorage(url: string): void {
  const link = document.createElement('a')
  link.href = toBrowserStorageUrl(url)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
