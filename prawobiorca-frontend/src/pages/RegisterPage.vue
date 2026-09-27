<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createAccount } from '@/api/generated/endpoints/account/account'
import AuthForm from '@/components/organisms/AuthForm.vue'

const router = useRouter()

async function register(username: string, password: string) {
  await createAccount({ username, password })

  ElMessage({
    message: 'Rejestracja przebiegła pomyślnie. Możesz się teraz zalogować.',
    type: 'success',
  })

  await router.push('/auth/login')
}
</script>

<template>
  <AuthForm
    title="Rejestracja"
    submit-label="Zarejestruj"
    password-autocomplete="new-password"
    link-text="Masz już konto? Zaloguj się"
    link-to="/auth/login"
    :error-message-options="{ conflictMessage: 'Nazwa użytkownika jest już zajęta.' }"
    :submit="register"
  />
</template>
