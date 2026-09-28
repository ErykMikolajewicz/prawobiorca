<script setup lang="ts">
import { reactive, ref } from 'vue'
import { getApiErrorMessage, type ApiErrorMessageOptions } from '@/utils/error'

type Props = {
  title: string
  submitLabel: string
  passwordAutocomplete: 'current-password' | 'new-password'
  linkText: string
  linkTo: string
  errorMessageOptions: ApiErrorMessageOptions
  submit: (username: string, password: string) => Promise<void>
}

const props = defineProps<Props>()

const form = reactive({
  username: '',
  password: '',
})

const errorMessage = ref('')
const isLoading = ref(false)

async function onSubmit() {
  if (!form.username || !form.password) {
    errorMessage.value = 'Wypełnij wszystkie pola.'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    await props.submit(form.username, form.password)
  } catch (error: unknown) {
    errorMessage.value = getApiErrorMessage(error, props.errorMessageOptions)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-container">
      <h2 class="title">{{ title }}</h2>

      <el-form :model="form" label-position="top" autocomplete="on" @submit.prevent="onSubmit">
        <el-alert
          v-if="errorMessage"
          :title="errorMessage"
          type="error"
          show-icon
          :closable="false"
        />

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
            :autocomplete="passwordAutocomplete"
            show-password
            required
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="isLoading" native-type="submit">
            {{ submitLabel }}
          </el-button>
        </el-form-item>
      </el-form>

      <p class="auth-link">
        <router-link v-slot="{ navigate, href }" :to="linkTo" custom>
          <el-link :href="href" type="primary" @click="navigate">{{ linkText }}</el-link>
        </router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

.auth-container {
  width: 100%;
  max-width: 400px;
  padding: 20px;
  box-sizing: border-box;
}

.title {
  text-align: center;
  margin-bottom: 24px;
}

.auth-link {
  text-align: center;
  margin-top: 16px;
}
</style>
