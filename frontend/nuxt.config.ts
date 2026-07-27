export default defineNuxtConfig({
  compatibilityDate: "2025-01-01",

  devtools: {
    enabled: true,
  },

  modules: ["@pinia/nuxt", "@vueuse/nuxt", "@nuxt/eslint"],

  css: ["~/assets/css/main.css"],

  postcss: {
    plugins: {
      "@tailwindcss/postcss": {},
    },
  },

  typescript: {
    strict: true,
  },

  runtimeConfig: {
    public: {
      apiUrl: "http://localhost:8000/api",
    },
  },
});
