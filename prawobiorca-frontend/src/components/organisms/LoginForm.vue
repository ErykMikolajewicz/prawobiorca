<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/error'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  password: '',
})

const errorMessage = ref('')
const isLoading = ref(false)

const onSubmit = async () => {
  if (!form.username || !form.password) {
    errorMessage.value = 'Wypełnij wszystkie pola.'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    await authStore.login(form.username, form.password)
    await router.push('/')
  } catch (error: unknown) {
    errorMessage.value = getApiErrorMessage(error, {
      unauthorizedMessage: 'Nieprawidłowa nazwa użytkownika lub hasło.',
    })
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <el-form :model="form" label-position="top" autocomplete="on" @submit.prevent="onSubmit">
    <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" />

    <el-form-item label="Nazwa użytkownika:" prop="username">
      <el-input
        id="username"
        v-model="form.username"
        name="username"
        autocomplete="username"
        required
      />
    </el-form-item>

    <el-form-item label="Hasło:" prop="password">
      <el-input
        id="password"
        v-model="form.password"
        type="password"
        name="password"
        autocomplete="current-password"
        show-password
        required
      />
    </el-form-item>

    <el-form-item>
      <el-button type="primary" :loading="isLoading" native-type="submit"> Zaloguj </el-button>
    </el-form-item>
  </el-form>
</template>
