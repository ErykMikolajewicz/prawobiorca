import { prawobiorcaClient } from '@/api/axios.ts'

export async function addDocumentToCase(caseId: string, presentationName: string, content: string) {
  const response = await prawobiorcaClient.post(`/api/user/cases/${caseId}/documents`, {
    presentationName: presentationName,
    content: content,
  })
  return response.data
}
