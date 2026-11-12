import axios from 'axios'
import { defineStore } from 'pinia'
import { ref } from 'vue'

import { checkIsUserLogged, logoutUser, logUser } from '@/api/generated/endpoints/auth/auth'
import type { CurrentUser } from '@/api/generated/model'
import { SessionExpiredError } from '@/api/sessionExpiry'

async function getCurrentUser(): Promise<CurrentUser | null> {
  try {
    return await checkIsUserLogged()
  } catch (error: unknown) {
    if (error instanceof SessionExpiredError) {
      return null
    }
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
  const isCheckingSession = ref(false)
  let sessionCheck: Promise<void> | null = null

  function checkIsLogged(): Promise<void> {
    if (sessionCheck) return sessionCheck

    isCheckingSession.value = true
    sessionCheck = getCurrentUser()
      .then((currentUser) => {
        isUserLogged.value = currentUser !== null
        isAdmin.value = currentUser?.isAdmin ?? false
      })
      .finally(() => {
        isCheckingSession.value = false
        sessionCheck = null
      })
    return sessionCheck
  }

  async function waitForSessionCheck(): Promise<void> {
    // The caller that starts the check reports errors; navigation can still continue.
    await sessionCheck?.catch(() => undefined)
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

  return {
    isUserLogged,
    isAdmin,
    isCheckingSession,
    checkIsLogged,
    waitForSessionCheck,
    login,
    logout,
    resetSession,
  }
})
