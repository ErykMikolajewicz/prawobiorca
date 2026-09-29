<script setup lang="ts">
import { ref } from 'vue'

const description = ref('')

const emit = defineEmits<{
  (e: 'generate-pdf', description: string): void
}>()

const handleSubmit = () => {
  emit('generate-pdf', description.value)
}
</script>

<template>
  <el-form @submit.prevent="handleSubmit">
    <el-form-item label="Opisz swoją sytuację lub cel pisma:" label-position="top">
      <el-input
        v-model="description"
        type="textarea"
        :rows="10"
        placeholder="np. Proszę o zapomogę finansową ze względu na trudną sytuację, w której znalazłem się po śmierci rodzica..."
      />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" native-type="submit"> Generuj Wniosek (PDF) </el-button>
    </el-form-item>
  </el-form>
</template>
