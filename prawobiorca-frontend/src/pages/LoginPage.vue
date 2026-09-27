<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AuthForm from '@/components/organisms/AuthForm.vue'

const router = useRouter()
const authStore = useAuthStore()

async function login(username: string, password: string) {
  await authStore.login(username, password)
  await router.push('/')
}
</script>

<template>
  <AuthForm
    title="Logowanie"
    submit-label="Zaloguj"
    password-autocomplete="current-password"
    link-text="Załóż konto"
    link-to="/accounts/register"
    :error-message-options="{ unauthorizedMessage: 'Nieprawidłowa nazwa użytkownika lub hasło.' }"
    :submit="login"
  />
</template>
