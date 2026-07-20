export default defineNuxtConfig({
  compatibilityDate: "2025-01-01",

  devtools: {
    enabled: true
  },

  modules: [
    "@pinia/nuxt",
    "@vueuse/nuxt",
    "@tailwindcss/postcss",
    "@nuxt/eslint"
  ],

  css: [
    "~/assets/css/main.css"
  ],

  typescript: {
    strict: true
  },

  runtimeConfig: {
    public: {
      apiUrl: "http://localhost:8000/api"
    }
  }
})
