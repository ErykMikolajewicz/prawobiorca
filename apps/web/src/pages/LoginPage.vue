<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AuthForm from '@/components/organisms/AuthForm.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

function getRedirectPath(): string {
  const redirect = route.query.redirect
  if (typeof redirect === 'string' && redirect.startsWith('/') && !redirect.startsWith('//')) {
    return redirect
  }
  return '/'
}

async function login(username: string, password: string) {
  await authStore.login(username, password)
  await router.push(getRedirectPath())
}
</script>

<template>
  <AuthForm
    title="Logowanie"
    submit-label="Zaloguj"
    password-autocomplete="current-password"
    link-text="Załóż konto"
    :link-to="{ name: 'RegisterPage' }"
    :error-message-options="{ unauthorizedMessage: 'Nieprawidłowa nazwa użytkownika lub hasło.' }"
    :submit="login"
  />
</template>
