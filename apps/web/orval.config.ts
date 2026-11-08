import { defineConfig } from 'orval'

export default defineConfig({
  prawobiorca: {
    input: {
      target: '../core-service/openapi.json',
      filters: {
        mode: 'exclude',
        tags: ['health check'],
      },
    },
    output: {
      mode: 'tags-split',
      client: 'axios-functions',
      target: 'src/api/generated/endpoints',
      schemas: 'src/api/generated/model',
      clean: true,
      formatter: 'oxfmt',
      override: {
        header: false,
        mutator: {
          path: 'src/api/axios.ts',
          name: 'prawobiorcaRequest',
        },
      },
    },
  },
})
