import axios from 'axios'

import type { RegulationUploadTarget } from '@/api/generated/model'

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
): Promise<void> {
  const formData = new FormData()
  for (const [key, value] of Object.entries(target.fields)) {
    formData.append(key, value)
  }
  formData.append('file', file)

  await axios.post(toBrowserStorageUrl(target.url), formData)
}

export function downloadFromStorage(url: string): void {
  const link = document.createElement('a')
  link.href = toBrowserStorageUrl(url)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
