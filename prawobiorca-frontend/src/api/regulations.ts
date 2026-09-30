import axios from 'axios'
import { prawobiorcaClient } from '@/api/axios'
import type {
  regulationData,
  regulationRepresentation,
  regulationType,
  regulationUploadResult,
  regulationUploadTarget,
} from '@/types/api/regulations.ts'
import type { searchParams, searchResult } from '@/types/api/search.ts'

function normalizeRegulation(regulation: regulationRepresentation): regulationRepresentation {
  return {
    ...regulation,
    preparationStatus: regulation.preparationStatus ?? 'NOT_STARTED',
  }
}

export async function getPublicRegulations(
  regulationType?: regulationType,
): Promise<Array<regulationRepresentation>> {
  try {
    const response = await prawobiorcaClient.get('/regulations', {
      params: regulationType ? { documentType: regulationType } : undefined,
    })

    if (response.status === 204) {
      return []
    }
    if (Array.isArray(response.data)) {
      return response.data.map(normalizeRegulation)
    }
    console.error('Invalid response format for public files:', response.data)
    return []
  } catch (error) {
    console.error('Failed to fetch public files:', error)
    return []
  }
}

export async function getUserRegulations(
  regulationType?: regulationType,
): Promise<Array<regulationRepresentation>> {
  try {
    const response = await prawobiorcaClient.get('/user/regulations', {
      params: regulationType ? { documentType: regulationType } : undefined,
    })

    if (response.status === 204) {
      return []
    }
    if (Array.isArray(response.data)) {
      return response.data.map(normalizeRegulation)
    }
    console.error('Invalid response format for user regulations:', response.data)
    return []
  } catch (error) {
    console.error('Failed to fetch user regulations:', error)
    return []
  }
}

export async function createPublicRegulation(
  data: regulationData,
): Promise<regulationUploadTarget> {
  const response = await prawobiorcaClient.post('/regulations', data)
  return response.data
}

export async function createUserRegulation(data: regulationData): Promise<regulationUploadTarget> {
  const response = await prawobiorcaClient.post('/user/regulations', data)
  return response.data
}

export async function uploadFileToStorage(
  target: regulationUploadTarget,
  file: File,
): Promise<void> {
  const formData = new FormData()
  for (const [key, value] of Object.entries(target.fields)) {
    formData.append(key, value)
  }
  formData.append('file', file)

  let uploadUrl = target.url
  if (import.meta.env.DEV && uploadUrl.includes('localhost:9000')) {
    uploadUrl = uploadUrl.replace(/^https?:\/\/localhost:9000/, '/storage')
  }

  await axios.post(uploadUrl, formData)
}

export async function confirmPublicRegulationUpload(regulationId: string): Promise<void> {
  await prawobiorcaClient.post(`/regulations/${regulationId}/confirm-upload`)
}

export async function confirmUserRegulationUpload(regulationId: string): Promise<void> {
  await prawobiorcaClient.post(`/user/regulations/${regulationId}/confirm-upload`)
}

export async function getPublicRegulationDownloadUrl(regulationId: string): Promise<string> {
  const response = await prawobiorcaClient.get(`/regulations/${regulationId}/download-url`)
  const url = response.data
  if (import.meta.env.DEV && typeof url === 'string' && url.includes('localhost:9000')) {
    return url.replace(/^https?:\/\/localhost:9000/, '/storage')
  }
  return url
}

export async function getUserRegulationDownloadUrl(regulationId: string): Promise<string> {
  const response = await prawobiorcaClient.get(`/user/regulations/${regulationId}/download-url`)
  const url = response.data
  if (import.meta.env.DEV && typeof url === 'string' && url.includes('localhost:9000')) {
    return url.replace(/^https?:\/\/localhost:9000/, '/storage')
  }
  return url
}

async function confirmUpload(
  regulationId: string,
  confirm: (regulationId: string) => Promise<void>,
): Promise<regulationUploadResult> {
  try {
    await confirm(regulationId)
    return { id: regulationId, preparationStatus: 'IN_PROGRESS' }
  } catch (error) {
    console.error('Failed to confirm regulation upload:', error)
    return { id: regulationId, preparationStatus: 'NOT_STARTED' }
  }
}

export async function uploadUserRegulation(
  regulation: File,
  presentationName: string,
  regulationType?: regulationType,
): Promise<regulationUploadResult> {
  try {
    const uploadTarget = await createUserRegulation({
      name: presentationName,
      regulationType: regulationType || null,
    })

    await uploadFileToStorage(uploadTarget, regulation)

    return await confirmUpload(uploadTarget.id, confirmUserRegulationUpload)
  } catch (error) {
    console.error('Failed to upload user regulation:', error)
    throw error
  }
}

export async function uploadPublicRegulation(
  regulation: File,
  presentationName: string,
  regulationType?: regulationType,
): Promise<regulationUploadResult> {
  try {
    const uploadTarget = await createPublicRegulation({
      name: presentationName,
      regulationType: regulationType || null,
    })

    await uploadFileToStorage(uploadTarget, regulation)

    return await confirmUpload(uploadTarget.id, confirmPublicRegulationUpload)
  } catch (error) {
    console.error('Failed to upload public regulation:', error)
    throw error
  }
}

export async function deleteUserRegulation(regulationId: string): Promise<void> {
  await prawobiorcaClient.delete(`/user/regulations/${regulationId}`)
}

export async function deletePublicRegulation(regulationId: string): Promise<void> {
  await prawobiorcaClient.delete(`/regulations/${regulationId}`)
}

export async function retryUserRegulationPreparation(regulationId: string): Promise<void> {
  await prawobiorcaClient.post(`/user/regulations/${regulationId}/preparation-retry`)
}

export async function retryPublicRegulationPreparation(regulationId: string): Promise<void> {
  await prawobiorcaClient.post(`/regulations/${regulationId}/preparation-retry`)
}

export async function searchRegulation(
  searchParams: searchParams,
  regulationId: string,
): Promise<Array<searchResult>> {
  const response = await prawobiorcaClient.get(`/regulations/${regulationId}/documents`, {
    params: { ...searchParams },
  })

  if (response.status === 204) {
    return []
  }
  return response.data
}

export async function searchUserRegulation(
  searchParams: searchParams,
  regulationId: string,
): Promise<Array<searchResult>> {
  const response = await prawobiorcaClient.get(`/user/regulations/${regulationId}/documents`, {
    params: { ...searchParams },
  })

  if (response.status === 204) {
    return []
  }
  return response.data
}
