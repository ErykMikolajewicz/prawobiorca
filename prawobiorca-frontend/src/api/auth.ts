import { prawobiorcaClient } from '@/api/axios'
import axios from 'axios'

export type currentUser = {
  isAdmin: boolean
}

export async function logout(): Promise<void> {
  await prawobiorcaClient.post('/api/auth/logout')
}

export async function login(username: string, password: string): Promise<void> {
  const params = new URLSearchParams()
  params.append('grant_type', 'password')
  params.append('username', username)
  params.append('password', password)

  await prawobiorcaClient.post('/api/auth/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
}

export async function getCurrentUser(): Promise<currentUser | null> {
  try {
    const response = await prawobiorcaClient.get('/api/auth/me')
    return response.data
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        return null
      }
    }
    throw error
  }
}
