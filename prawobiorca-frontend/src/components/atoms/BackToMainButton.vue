<script setup lang="ts">
import { ArrowLeft } from '@element-plus/icons-vue'
</script>

<template>
  <router-link v-slot="{ navigate }" :to="{ name: 'MainPage' }" custom>
    <el-button link @click="navigate">
      <el-icon><ArrowLeft /></el-icon> Powrót do głównego ekranu
    </el-button>
  </router-link>
</template>
