import axios from 'axios'
import { defineStore } from 'pinia'
import { ref } from 'vue'

import { checkIsUserLogged, logoutUser, logUser } from '@/api/generated/endpoints/auth/auth'
import type { CurrentUser } from '@/api/generated/model'

async function getCurrentUser(): Promise<CurrentUser | null> {
  try {
    return await checkIsUserLogged()
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        return null
      }
    }
    throw error
  }
}

export const useAuthStore = defineStore('auth', () => {
  const isUserLogged = ref(false)
  const isAdmin = ref(false)

  async function checkIsLogged(): Promise<void> {
    const currentUser = await getCurrentUser()
    isUserLogged.value = currentUser !== null
    isAdmin.value = currentUser?.isAdmin ?? false
  }

  async function login(username: string, password: string): Promise<void> {
    await logUser({ grant_type: 'password', username, password })
    isUserLogged.value = true

    const currentUser = await getCurrentUser()
    isAdmin.value = currentUser?.isAdmin ?? false
  }

  function resetSession(): void {
    isUserLogged.value = false
    isAdmin.value = false
  }

  async function logout() {
    try {
      await logoutUser()
    } finally {
      resetSession()
    }
  }

  return { isUserLogged, isAdmin, checkIsLogged, login, logout, resetSession }
})
