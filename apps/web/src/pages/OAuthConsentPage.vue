<script setup lang="ts">
import { onBeforeMount, ref } from 'vue'
import { useRoute } from 'vue-router'
import { showApiError } from '@/utils/error'

import AppLayout from '@/components/templates/AppLayout.vue'

import { getConsentDetails, grantConsent } from '@/api/generated/endpoints/oauth/oauth'

import type { AuthorizationRequest } from '@/api/generated/model'

const route = useRoute()

const clientName = ref<string | null>(null)
const isLoading = ref(false)
const isGranting = ref(false)

function getQueryParam(name: string): string | undefined {
  const value = route.query[name]
  return typeof value === 'string' ? value : undefined
}

function readAuthorizationRequest(): AuthorizationRequest {
  return {
    clientId: getQueryParam('clientId') ?? '',
    redirectUri: getQueryParam('redirectUri') ?? '',
    resource: getQueryParam('resource') ?? '',
    codeChallenge: getQueryParam('codeChallenge') ?? '',
    state: getQueryParam('state') ?? null,
  }
}

const authorizationRequest = readAuthorizationRequest()

async function loadDetails() {
  isLoading.value = true
  try {
    const details = await getConsentDetails(authorizationRequest)
    clientName.value = details.clientName
  } catch {
    clientName.value = null
  } finally {
    isLoading.value = false
  }
}

async function handleGrant() {
  isGranting.value = true
  try {
    const { redirectUrl } = await grantConsent(authorizationRequest)
    window.location.assign(redirectUrl)
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się udzielić dostępu.' })
    isGranting.value = false
  }
}

function handleDeny() {
  const redirectUrl = new URL(authorizationRequest.redirectUri)
  redirectUrl.searchParams.set('error', 'access_denied')
  if (authorizationRequest.state) {
    redirectUrl.searchParams.set('state', authorizationRequest.state)
  }
  window.location.assign(redirectUrl.toString())
}

onBeforeMount(loadDetails)
</script>

<template>
  <AppLayout>
    <div v-loading="isLoading" class="consent-page">
      <el-card v-if="clientName" shadow="never" class="app-card">
        <template #header>Prośba o dostęp</template>
        <p>
          Aplikacja <strong>{{ clientName }}</strong> prosi o dostęp do wyszukiwarki aktów prawnych
          w Twoim imieniu przez MCP. Wyszukiwania będą rozliczane z miesięcznego budżetu MCP.
        </p>
        <el-button @click="handleDeny">Odmów</el-button>
        <el-button type="primary" :loading="isGranting" @click="handleGrant">Zezwól</el-button>
      </el-card>
      <el-result
        v-else-if="!isLoading"
        icon="error"
        title="Nieprawidłowa prośba o dostęp"
        sub-title="Sprawdź konfigurację klienta MCP i spróbuj połączyć się ponownie."
      />
    </div>
  </AppLayout>
</template>

<style scoped>
.consent-page {
  min-height: 120px;
  max-width: 560px;
}
</style>
