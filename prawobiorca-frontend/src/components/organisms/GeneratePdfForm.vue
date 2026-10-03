<script setup lang="ts">
import { reactive } from 'vue'

import type { NewApplication } from '@/api/generated/model'

const form = reactive<NewApplication>({
  description: '',
  userName: '',
  studentId: '',
  department: '',
  semester: '',
  title: '',
})

const emit = defineEmits<{
  (e: 'generate-pdf', newApplication: NewApplication): void
}>()

const handleSubmit = () => {
  emit('generate-pdf', { ...form })
}
</script>

<template>
  <el-form :model="form" label-position="top" @submit.prevent="handleSubmit">
    <el-form-item label="Imię i nazwisko:">
      <el-input v-model="form.userName" required />
    </el-form-item>
    <el-form-item label="Numer albumu:">
      <el-input v-model="form.studentId" required />
    </el-form-item>
    <el-form-item label="Wydział:">
      <el-input v-model="form.department" required />
    </el-form-item>
    <el-form-item label="Semestr:">
      <el-input v-model="form.semester" required />
    </el-form-item>
    <el-form-item label="Tytuł zawodowy:">
      <el-input v-model="form.title" />
    </el-form-item>
    <el-form-item label="Opisz swoją sytuację lub cel pisma:">
      <el-input
        v-model="form.description"
        type="textarea"
        :rows="10"
        placeholder="np. Proszę o zapomogę finansową ze względu na trudną sytuację, w której znalazłem się po śmierci rodzica..."
        required
      />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" native-type="submit"> Generuj Wniosek (DOCX) </el-button>
    </el-form-item>
  </el-form>
</template>
