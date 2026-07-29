<script setup lang="ts">
import AppLogo from "~/components/AppLogo.vue";
import AppButton from "~/components/buttons/AppButton.vue";
import IconCheck from "~/components/icons/IconCheck.vue";
import { useAuth } from "~/composables/useAuth";

definePageMeta({ layout: false });

const { logout } = useAuth();

onMounted(async () => {
  await logout();
});
</script>

<template>
  <div
    class="flex min-h-screen items-center justify-center bg-gradient-to-br from-sup-light-green/10 via-sup-light-gray to-sup-light-gray px-6 py-10"
  >
    <div
      class="w-full max-w-md rounded-2xl border border-sup-border bg-sup-withe p-8 text-center shadow-lg sm:max-w-lg sm:p-10 lg:max-w-xl lg:p-12"
    >
      <AppLogo size="md" />

      <div
        class="mx-auto mt-8 flex h-16 w-16 items-center justify-center rounded-full bg-sup-light-green/15 text-sup-dark-green sm:h-20 sm:w-20"
      >
        <IconCheck size="lg" />
      </div>

      <h1 class="mt-6 text-2xl font-bold text-sup-very-gray sm:text-3xl">
        Vous êtes déconnecté
      </h1>
      <p class="mt-3 text-sm text-gray-500 sm:text-base">
        Vous avez été déconnecté de votre compte SUPMEAL en toute sécurité.
      </p>

      <div class="mt-8 flex flex-col gap-3">
        <AppButton to="/login" variant="primary" size="lg" block
          >Se reconnecter</AppButton
        >
        <NuxtLink
          to="/"
          class="text-sm font-semibold text-sup-dark-green hover:underline sm:text-base"
        >
          Retour à l'accueil
        </NuxtLink>
      </div>
    </div>
  </div>
</template>
