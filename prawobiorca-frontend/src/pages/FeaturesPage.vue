<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import FolderRoundedIcon from '@iconify-vue/material-symbols/folder-rounded'
import DescriptionRoundedIcon from '@iconify-vue/material-symbols/description-rounded'
import UploadFileRoundedIcon from '@iconify-vue/material-symbols/upload-file-rounded'

import AppLayout from '@/components/templates/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const { isUserLogged } = storeToRefs(useAuthStore())

const features = [
  {
    icon: FolderRoundedIcon,
    title: 'Zarządzanie sprawami',
    description: 'Twórz sprawy i przypinaj do nich przepisy, które są dla Ciebie istotne.',
  },
  {
    icon: DescriptionRoundedIcon,
    title: 'Generowanie wniosków',
    description: 'Generuj wnioski na podstawie szablonów i danych z Twojej sprawy.',
  },
  {
    icon: UploadFileRoundedIcon,
    title: 'Własne regulacje',
    description: 'Dodawaj własne pliki i przeszukuj je tak samo jak regulacje publiczne.',
  },
]
</script>

<template>
  <AppLayout>
    <h1 class="features-title">Funkcje dla zalogowanych użytkowników</h1>

    <ul class="features">
      <li v-for="feature in features" :key="feature.title" class="feature">
        <span class="feature-icon">
          <component :is="feature.icon" />
        </span>
        <div>
          <p class="feature-title">{{ feature.title }}</p>
          <p class="feature-description">{{ feature.description }}</p>
        </div>
      </li>
    </ul>

    <div v-if="!isUserLogged" class="features-actions">
      <el-button type="primary" @click="router.push({ name: 'LoginPage' })">Zaloguj się</el-button>
      <el-button @click="router.push({ name: 'RegisterPage' })">Załóż konto</el-button>
    </div>
  </AppLayout>
</template>

<style scoped>
.features-title {
  margin: 0 0 var(--app-space-xl);
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.features {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-lg);
  margin: 0 0 var(--app-space-xl);
  padding: 0;
  list-style: none;
}

.feature {
  display: flex;
  align-items: center;
  gap: var(--app-space-md);
  padding: var(--app-space-lg);
  border: 1px solid var(--app-card-border);
  border-radius: var(--app-radius-lg);
  background: var(--app-card-bg);
}

.feature-icon {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 50%;
  font-size: 1.5rem;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-8);
}

.feature-title {
  margin: 0;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.feature-description {
  margin: var(--app-space-xs) 0 0;
  font-size: 0.875rem;
  color: var(--el-text-color-secondary);
}

.features-actions {
  display: flex;
  gap: var(--app-space-sm);
}

.features-actions .el-button + .el-button {
  margin-left: 0;
}
</style>
