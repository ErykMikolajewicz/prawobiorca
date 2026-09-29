import { prawobiorcaClient } from '@/api/axios'

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
