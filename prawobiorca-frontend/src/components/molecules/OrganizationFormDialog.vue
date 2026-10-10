<script setup lang="ts">
import { computed, reactive, watch } from 'vue'

type Props = {
  title: string
  withShortName?: boolean
  initialName?: string
  initialShortName?: string
  submitting?: boolean
}

const props = defineProps<Props>()

const visible = defineModel<boolean>({ required: true })

const emit = defineEmits<{
  (e: 'submit', name: string, shortName: string): void
}>()

const form = reactive({ name: '', shortName: '' })

const isValid = computed(
  () => form.name.trim() !== '' && (!props.withShortName || form.shortName.trim() !== ''),
)

watch(visible, (isVisible) => {
  if (isVisible) {
    form.name = props.initialName ?? ''
    form.shortName = props.initialShortName ?? ''
  }
})

function handleSubmit() {
  if (!isValid.value) {
    return
  }
  emit('submit', form.name.trim(), form.shortName.trim())
}
</script>

<template>
  <el-dialog v-model="visible" :title="title" width="min(480px, 92vw)">
    <el-form label-position="top" @submit.prevent="handleSubmit">
      <el-form-item label="Nazwa:">
        <el-input v-model="form.name" :maxlength="255" placeholder="np. Politechnika Wrocławska" />
      </el-form-item>

      <el-form-item v-if="withShortName" label="Skrót:">
        <el-input v-model="form.shortName" :maxlength="32" placeholder="np. PWr" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">Anuluj</el-button>
      <el-button type="primary" :loading="submitting" :disabled="!isValid" @click="handleSubmit">
        Zapisz
      </el-button>
    </template>
  </el-dialog>
</template>
