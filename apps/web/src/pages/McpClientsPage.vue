<script setup lang="ts">
import { computed, onBeforeMount, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'

import AppLayout from '@/components/templates/AppLayout.vue'

import {
  createOauthClient,
  deleteOauthClient,
  getOauthClients,
} from '@/api/generated/endpoints/oauth-clients/oauth-clients'

import type { CreatedOAuthClient, OAuthClientData } from '@/api/generated/model'

const MAX_NAME_LENGTH = 100

const clients = ref<Array<OAuthClientData>>([])
const isLoading = ref(false)
const isDialogVisible = ref(false)
const isSubmitting = ref(false)
const newClientName = ref('')
const createdClient = ref<CreatedOAuthClient | null>(null)

const mcpUrl = `${window.location.origin}/api/mcp`
const isNameValid = computed(() => newClientName.value.trim() !== '')

function formatDate(date: string) {
  return new Date(date).toLocaleString('pl-PL', { dateStyle: 'short', timeStyle: 'short' })
}

async function loadClients() {
  isLoading.value = true
  try {
    clients.value = await getOauthClients()
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się pobrać klientów MCP.' })
  } finally {
    isLoading.value = false
  }
}

function openDialog() {
  newClientName.value = ''
  isDialogVisible.value = true
}

async function handleCreate() {
  if (!isNameValid.value) {
    return
  }
  isSubmitting.value = true
  try {
    createdClient.value = await createOauthClient({ name: newClientName.value.trim() })
    isDialogVisible.value = false
    await loadClients()
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się dodać klienta MCP.' })
  } finally {
    isSubmitting.value = false
  }
}

async function handleDelete(clientId: string) {
  try {
    await deleteOauthClient(clientId)
    ElMessage.success('Klient MCP został usunięty.')
    if (createdClient.value?.id === clientId) {
      createdClient.value = null
    }
    await loadClients()
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się usunąć klienta MCP.' })
  }
}

onBeforeMount(loadClients)
</script>

<template>
  <AppLayout>
    <div class="page-header">
      <h1 class="page-title">Klienci MCP</h1>
      <el-button type="primary" @click="openDialog">Dodaj klienta</el-button>
    </div>

    <el-card v-if="createdClient" shadow="never" class="app-card created-client">
      <template #header>Dane nowego klienta</template>
      <el-alert
        type="warning"
        :closable="false"
        title="Zapisz sekret teraz – nie będzie można go wyświetlić ponownie."
      />
      <dl class="server-address">
        <dt>Adres serwera MCP</dt>
        <dd>
          <code>{{ mcpUrl }}</code>
        </dd>
      </dl>
      <el-form label-position="top">
        <el-form-item label="Client ID">
          <el-input :model-value="createdClient.id" readonly />
        </el-form-item>
        <el-form-item label="Client Secret">
          <el-input :model-value="createdClient.secret" readonly />
        </el-form-item>
      </el-form>
      <p class="created-client-hint">
        W Claude dodaj własny konektor z adresem serwera MCP, a w ustawieniach zaawansowanych podaj
        Client ID i Client Secret.
      </p>
      <el-button @click="createdClient = null">Gotowe</el-button>
    </el-card>

    <el-table v-loading="isLoading" :data="clients" empty-text="Brak klientów MCP.">
      <el-table-column prop="name" label="Nazwa" />
      <el-table-column label="Utworzono" width="180">
        <template #default="{ row }">{{ formatDate(row.createDate) }}</template>
      </el-table-column>
      <el-table-column width="120" align="right">
        <template #default="{ row }">
          <el-popconfirm
            title="Czy na pewno chcesz usunąć tego klienta? Jego połączenia przestaną działać."
            confirm-button-text="Tak"
            cancel-button-text="Nie"
            :width="260"
            @confirm="handleDelete(row.id)"
          >
            <template #reference>
              <el-button type="danger" plain size="small">Usuń</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="isDialogVisible" title="Dodaj klienta MCP" width="min(480px, 92vw)">
      <el-form label-position="top" @submit.prevent="handleCreate">
        <el-form-item label="Nazwa:">
          <el-input v-model="newClientName" :maxlength="MAX_NAME_LENGTH" placeholder="np. Claude" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="isDialogVisible = false">Anuluj</el-button>
        <el-button
          type="primary"
          :loading="isSubmitting"
          :disabled="!isNameValid"
          @click="handleCreate"
        >
          Zapisz
        </el-button>
      </template>
    </el-dialog>
  </AppLayout>
</template>

<style scoped>
.created-client {
  margin-bottom: var(--app-space-lg);
  max-width: 640px;
}

.server-address {
  margin-block: var(--app-space-md);
}

.server-address dd {
  margin-inline-start: 0;
  overflow-wrap: anywhere;
}

.server-address code {
  user-select: all;
}

.created-client-hint {
  margin: 0 0 var(--app-space-md);
}
</style>
