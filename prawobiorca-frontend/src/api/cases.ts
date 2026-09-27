import { prawobiorcaClient } from '@/api/axios'
import type { caseData } from '@/types/api/cases.ts'
import type { DocumentData } from '@/types/api/documents.ts'

export async function getCases(): Promise<Array<caseData>> {
  try {
    const response = await prawobiorcaClient.get('/api/user/cases')
    if (response.status == 204) {
      return []
    }
    if (Array.isArray(response.data)) {
      return response.data
    }
    console.error('Invalid response format for cases:', response.data)
    return []
  } catch (error) {
    console.error('Failed to fetch cases:', error)
    return []
  }
}

export async function getCaseDocuments(caseId: string): Promise<Array<DocumentData>> {
  try {
    const response = await prawobiorcaClient.get(`/api/user/cases/${caseId}/documents`)
    if (response.status == 204) {
      return []
    }
    if (Array.isArray(response.data)) {
      return response.data
    }
    console.error('Invalid response format for case articles:', response.data)
    return []
  } catch (error) {
    console.error('Failed to fetch case articles:', error)
    return []
  }
}

export async function addCase(caseName: string): Promise<string> {
  const params = new URLSearchParams()
  params.append('caseName', caseName)
  const response = await prawobiorcaClient.post('/api/user/cases', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return response.data
}

export async function deleteCase(caseId: string): Promise<void> {
  await prawobiorcaClient.delete(`/api/user/cases/${caseId}`)
}

export async function unpinDocument(articleId: string): Promise<void> {
  await prawobiorcaClient.delete(`/api/user/cases/documents/${articleId}`)
}

export async function generatePdf(caseId: string, description: string): Promise<void> {
  const response = await prawobiorcaClient.post(
    '/api/case/generate-pdf',
    { description, caseId },
    { responseType: 'blob' },
  )

  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `wniosek_${caseId}.pdf`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
