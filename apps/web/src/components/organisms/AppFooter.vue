<template>
  <el-footer class="app-footer">
    <p class="footer-text">
      Prawobiorca. Aplikacja stworzona w celu pomocy studentom w korzystaniu z ich praw.
    </p>
  </el-footer>
</template>

<style scoped>
.app-footer {
  background-color: transparent;
  border-top: 1px solid var(--app-border-color);

  display: flex;
  align-items: center;
  padding: 0 var(--app-space-lg);
}

.footer-text {
  color: var(--el-text-color-regular);
  font-size: 0.875rem;
  margin: 0;
  text-align: left;
}
</style>
