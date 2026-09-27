<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createAccount } from '@/api/generated/endpoints/account/account'
import { ElMessage } from 'element-plus'
import { getApiErrorMessage } from '@/utils/error'

const router = useRouter()

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
    await createAccount({ username: form.username, password: form.password })

    ElMessage({
      message: 'Rejestracja przebiegła pomyślnie. Możesz się teraz zalogować.',
      type: 'success',
    })

    await router.push('/auth/login')
  } catch (error: unknown) {
    errorMessage.value = getApiErrorMessage(error, {
      conflictMessage: 'Nazwa użytkownika jest już zajęta.',
    })
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <el-form :model="form" label-position="top" @submit.prevent="onSubmit">
    <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" />

    <el-form-item label="Nazwa użytkownika:" prop="username">
      <el-input id="username" v-model="form.username" required />
    </el-form-item>

    <el-form-item label="Hasło:" prop="password">
      <el-input
        id="password"
        v-model="form.password"
        type="password"
        autocomplete="new-password"
        show-password
        required
      />
    </el-form-item>

    <el-form-item>
      <el-button type="primary" :loading="isLoading" native-type="submit"> Zarejestruj </el-button>
    </el-form-item>
  </el-form>
</template>
