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
      setupFiles: ['src/__tests__/setup.ts'],
      server: { deps: { inline: ['element-plus'] } },
      coverage: {
        include: ['src/**/*.{ts,vue}'],
        exclude: ['src/api/generated/**', 'src/**/__tests__/**'],
        thresholds: {
          statements: 90,
          branches: 90,
          functions: 90,
          lines: 90,
        },
      },
    },
  }),
)
