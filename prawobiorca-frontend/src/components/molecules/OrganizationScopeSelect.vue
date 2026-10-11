<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useOrganizationsStore } from '@/stores/organizations'

type Props = {
  inline?: boolean
}

defineProps<Props>()

const organizationId = defineModel<string>('organizationId', { required: true })
const suborganizationId = defineModel<string>('suborganizationId', { required: true })

const { organizations } = storeToRefs(useOrganizationsStore())

const suborganizations = computed(
  () =>
    organizations.value.find((organization) => organization.id === organizationId.value)
      ?.suborganizations ?? [],
)

function handleOrganizationChange() {
  suborganizationId.value = ''
}
</script>

<template>
  <el-row :gutter="inline ? 24 : 0">
    <el-col :span="inline ? 12 : 24" :xs="24">
      <el-form-item label="Organizacja (opcjonalnie):">
        <el-select
          v-model="organizationId"
          clearable
          placeholder="Ogólny"
          @change="handleOrganizationChange"
        >
          <el-option
            v-for="organization in organizations"
            :key="organization.id"
            :label="organization.name"
            :value="organization.id"
          />
        </el-select>
      </el-form-item>
    </el-col>

    <el-col :span="inline ? 12 : 24" :xs="24">
      <el-form-item label="Podorganizacja (opcjonalnie):">
        <el-select
          v-model="suborganizationId"
          :disabled="!organizationId"
          clearable
          placeholder="Wszystkie podorganizacje"
        >
          <el-option
            v-for="suborganization in suborganizations"
            :key="suborganization.id"
            :label="suborganization.name"
            :value="suborganization.id"
          />
        </el-select>
      </el-form-item>
    </el-col>
  </el-row>
</template>
