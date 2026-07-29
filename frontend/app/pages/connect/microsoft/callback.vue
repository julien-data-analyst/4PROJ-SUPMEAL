<script setup lang="ts">
import AppLogo from "~/components/AppLogo.vue";
import { useOAuth } from "~/composables/useOAuth";

definePageMeta({ layout: "empty" });

const { finishOAuth } = useOAuth();

const error = ref("");

onMounted(async () => {
  try {
    await finishOAuth("microsoft");
    await navigateTo("/home");
  } catch (cause) {
    error.value =
      cause instanceof Error
        ? cause.message
        : "La connexion Microsoft a échoué.";
  }
});
</script>

<template>
  <div
    class="flex min-h-screen items-center justify-center bg-gradient-to-br from-sup-light-green/10 via-sup-light-gray to-sup-light-gray px-6 py-10"
  >
    <div
      class="w-full max-w-md rounded-2xl border border-sup-border bg-sup-withe p-8 text-center shadow-lg"
    >
      <AppLogo size="md" />

      <p v-if="!error" class="mt-6 text-sm text-gray-500 sm:text-base">
        Connexion à votre compte Microsoft...
      </p>

      <template v-else>
        <p class="mt-6 text-sm text-sup-red-error">{{ error }}</p>
        <NuxtLink
          to="/login"
          class="mt-4 inline-block font-semibold text-sup-dark-green"
        >
          Retour à la connexion
        </NuxtLink>
      </template>
    </div>
  </div>
</template>
