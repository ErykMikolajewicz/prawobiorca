<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import FolderRoundedIcon from '@iconify-vue/material-symbols/folder-rounded'
import DescriptionRoundedIcon from '@iconify-vue/material-symbols/description-rounded'
import UploadFileRoundedIcon from '@iconify-vue/material-symbols/upload-file-rounded'

import AppLayout from '@/components/templates/AppLayout.vue'
import FeatureItem from '@/components/molecules/FeatureItem.vue'
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
    <div class="page-header">
      <h1 class="page-title">Funkcje dla zalogowanych użytkowników</h1>
    </div>

    <ul class="features app-list-reset">
      <li v-for="feature in features" :key="feature.title" class="feature">
        <FeatureItem
          :icon="feature.icon"
          :title="feature.title"
          :description="feature.description"
        />
      </li>
    </ul>

    <div v-if="!isUserLogged" class="app-actions">
      <el-button type="primary" @click="router.push({ name: 'LoginPage' })">Zaloguj się</el-button>
      <el-button @click="router.push({ name: 'RegisterPage' })">Załóż konto</el-button>
    </div>
  </AppLayout>
</template>

<style scoped>
.features {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-lg);
  margin: 0 0 var(--app-space-xl);
}

.feature {
  padding: var(--app-space-lg);
  border: 1px solid var(--app-card-border);
  border-radius: var(--app-radius-lg);
  background: var(--app-card-bg);
}
</style>
