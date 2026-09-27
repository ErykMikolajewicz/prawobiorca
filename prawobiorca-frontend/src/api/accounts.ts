import { prawobiorcaClient } from '@/api/axios'

export async function register(username: string, password: string): Promise<void> {
  await prawobiorcaClient.post('/api/accounts/register', {
    username,
    password,
  })
}
