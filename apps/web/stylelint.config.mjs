export default {
  extends: ['stylelint-config-standard', 'stylelint-config-recommended-vue'],
  rules: {
    'custom-property-empty-line-before': null,
    'declaration-empty-line-before': null,
    'max-nesting-depth': 0,
    'color-no-hex': true,
    'function-disallowed-list': ['rgb', 'rgba', 'hsl', 'hsla'],
    'selector-class-pattern': [
      '^(el-[a-z0-9_-]+|[a-z][a-z0-9]*(-[a-z0-9]+)*)$',
      { message: 'Expected class selector to be kebab-case' },
    ],
    'declaration-property-unit-allowed-list': { 'font-size': ['rem'] },
  },
  overrides: [
    {
      files: ['src/assets/styles/tokens.css', 'src/assets/styles/overrides.css'],
      rules: {
        'color-no-hex': null,
        'function-disallowed-list': null,
      },
    },
  ],
}
