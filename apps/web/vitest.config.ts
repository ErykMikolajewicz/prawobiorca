import { fileURLToPath } from 'node:url'
import { mergeConfig, defineConfig, configDefaults } from 'vitest/config'
import viteConfig from './vite.config.ts'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      exclude: [...configDefaults.exclude, 'e2e/**'],
      root: fileURLToPath(new URL('./', import.meta.url)),
      coverage: {
        include: ['src/**/*.{ts,vue}'],
        exclude: ['src/api/generated/**', 'src/**/__tests__/**'],
        thresholds: {
          statements: 45,
          branches: 40,
          functions: 35,
          lines: 45,
        },
      },
    },
  }),
)
