import { PluginKind, declareValuePlugin } from '@stryker-mutator/api/plugin'

const macros = new Set([
  'defineProps',
  'defineEmits',
  'defineExpose',
  'defineOptions',
  'defineSlots',
  'defineModel',
  'withDefaults',
])

export const strykerPlugins = [
  declareValuePlugin(PluginKind.Ignore, 'vue-macros', {
    shouldIgnore(path) {
      const expression = path.isExpressionStatement() ? path.get('expression') : path
      if (expression.isCallExpression()) {
        const callee = expression.get('callee')
        if (callee.isIdentifier() && macros.has(callee.node.name)) {
          return 'Vue compiler macros must remain statically analyzable at the top level.'
        }
      }
      return undefined
    },
  }),
]
