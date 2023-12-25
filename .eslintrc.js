module.exports = {
  root: true,
  env: {
    node: true,
  },
  parser: 'vue-eslint-parser',
  extends: [
    // add more generic rulesets here, such as:
    'plugin:vue/essential',
    'eslint:recommended',
  ],
  plugins: ['vuetify'],
  rules: {
    // override/add rules settings here, such as:
    "vuetify/no-deprecated-classes": "error",
    "vuetify/grid-unknown-attributes": "error",
    "vuetify/no-legacy-grid": "error",
    "camelcase": "off",
    "vue/multi-word-component-names": ["warn"],
    "vue/no-unused-vars": "error",
    "vue/no-mutating-props": "warn",
  }
}
