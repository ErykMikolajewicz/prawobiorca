import { globalIgnores } from 'eslint/config'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'
import pluginVitest from '@vitest/eslint-plugin'
import pluginOxlint from 'eslint-plugin-oxlint'
import pluginSonarjs from 'eslint-plugin-sonarjs'

export default defineConfigWithVueTs(
  {
    name: 'app/files-to-lint',
    files: ['**/*.{vue,ts,mts,tsx}'],
  },

  globalIgnores(['**/dist/**', '**/dist-ssr/**', '**/coverage/**', 'src/api/generated/**']),

  ...pluginVue.configs['flat/recommended'],
  vueTsConfigs.strictTypeChecked,

  {
    plugins: { sonarjs: pluginSonarjs },
    rules: {
      'sonarjs/cognitive-complexity': ['error', 15],
      'vue/max-template-depth': ['error', { maxDepth: 8 }],
      'vue/max-lines-per-block': ['error', { template: 150, script: 150 }],
      'vue/max-attributes-per-line': 'off',
      'vue/singleline-html-element-content-newline': 'off',
      'vue/html-indent': 'off',
      'vue/html-self-closing': 'off',
      'vue/no-v-html': 'error',
      'no-new-func': 'error',
      '@typescript-eslint/no-confusing-void-expression': ['error', { ignoreArrowShorthand: true }],
    },
  },

  {
    files: ['**/*.vue'],
    rules: {
      '@typescript-eslint/unified-signatures': 'off',
    },
  },

  {
    ...pluginVitest.configs.recommended,
    files: ['src/**/__tests__/**'],
  },

  {
    files: ['src/**/__tests__/**'],
    rules: {
      '@typescript-eslint/unbound-method': 'off',
      '@typescript-eslint/no-non-null-assertion': 'off',
    },
  },

  ...pluginOxlint.buildFromOxlintConfigFile('.oxlintrc.json')
)
