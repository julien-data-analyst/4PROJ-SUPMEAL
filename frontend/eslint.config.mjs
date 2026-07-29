// @ts-check
import withNuxt from "./.nuxt/eslint.config.mjs";

export default withNuxt(
  // Your custom configs here
  {
    rules: {
      // Conflicts with Prettier's own void-element self-closing style
      // (eslint-plugin-vue wants `<input>`, Prettier wants `<input />`),
      // which made the two `--fix`/`--write` steps fight each other.
      // Prettier owns formatting here.
      "vue/html-self-closing": "off",
    },
  },
);
