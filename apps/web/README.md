# Prawobiorca Frontend

The frontend layer of **Prawobiorca** --- a Vue 3 single-page application.

It is part of the main Prawobiorca repository; see the root [README](../README.md) for the project overview and
[Frontend documentation](../docs/architecture/frontend.md) for the stack, project structure and API integration.

## Recommended IDE
It is recommended to use a JetBrains IDE, preferably PyCharm, with frontend plugins.
For students, PyCharm Professional is free for non-commercial use.

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Project Setup

All commands below are run from this directory (`prawobiorca-frontend/`).

```sh
pnpm install
```

### Compile and Hot-Reload for Development

```sh
pnpm dev
```

### Type-Check, Compile and Minify for Production

```sh
pnpm build
```

### Run Unit Tests with [Vitest](https://vitest.dev/)

```sh
pnpm test:unit
```

### Lint with [Oxlint](https://oxc.rs/docs/guide/usage/linter) and [ESLint](https://eslint.org/)

```sh
pnpm lint
```

### Format with [Oxfmt](https://oxc.rs/docs/guide/usage/formatter)

```sh
pnpm format
```

### Check Lint and Formatting Without Fixing

```sh
pnpm check
```
