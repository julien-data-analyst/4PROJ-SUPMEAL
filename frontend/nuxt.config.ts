export default defineNuxtConfig({
  compatibilityDate: "2025-01-01",

  devtools: {
    enabled: true,
  },

  modules: ["@pinia/nuxt", "@vueuse/nuxt", "@nuxt/eslint"],

  css: ["~/assets/css/main.css"],

  app: {
    head: {
      link: [
        { rel: "icon", type: "image/png", href: "/Logo%20entreprise.png" },
      ],
    },
  },

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
      apiUrl: `http://localhost:${process.env.BACKEND_PORT || 8000}/api`,
      azureClientId: process.env.AZURE_CLIENT_ID || "",
      azureAuthority:
        process.env.AZURE_AUTHORITY ||
        "https://login.microsoftonline.com/common/v2.0",
      azureRedirectUri:
        process.env.AZURE_REDIRECT_URI ||
        "http://localhost:3000/connect/microsoft/callback",
    },
  },
});
