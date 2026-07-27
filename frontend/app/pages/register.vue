<script setup lang="ts">
import AppLogo from "~/components/AppLogo.vue";
import AppInput from "~/components/forms/AppInput.vue";
import AppButton from "~/components/buttons/AppButton.vue";
import OAuthButtons from "~/components/buttons/OAuthButtons.vue";
import IconMail from "~/components/icons/IconMail.vue";
import IconUser from "~/components/icons/IconUser.vue";

definePageMeta({ layout: false });

const username = ref("");
const email = ref("");
const password = ref("");
const passwordConfirm = ref("");
const acceptTerms = ref(false);
</script>

<template>
  <div
    class="flex min-h-screen items-center justify-center bg-gradient-to-br from-sup-light-green/10 via-sup-light-gray to-sup-light-gray px-6 py-10"
  >
    <div
      class="w-full max-w-lg rounded-2xl border border-sup-border bg-sup-withe p-8 shadow-lg sm:max-w-xl sm:p-10 lg:max-w-2xl lg:p-12"
    >
      <AppLogo size="lg" tagline="Vos recettes, cookbooks & plannings au même endroit" />

      <h1 class="mt-8 text-center text-2xl font-bold text-sup-very-gray sm:text-3xl">
        Créer un compte
      </h1>
      <p class="mb-8 mt-2 text-center text-sm text-gray-500 sm:text-base">
        Rejoignez la communauté SUPMEAL
      </p>

      <OAuthButtons />

      <div class="mb-6 flex items-center gap-3">
        <div class="h-px flex-1 bg-sup-border" />
        <span class="text-xs font-medium text-gray-400 sm:text-sm">OU PAR EMAIL</span>
        <div class="h-px flex-1 bg-sup-border" />
      </div>

      <form @submit.prevent>
        <AppInput
          id="username"
          v-model="username"
          type="text"
          label="Nom d'utilisateur"
          placeholder="johndoe"
          autocomplete="username"
        >
          <template #icon><IconUser size="sm" /></template>
        </AppInput>

        <AppInput
          id="email"
          v-model="email"
          type="email"
          label="Adresse email"
          placeholder="john.doe@email.com"
          autocomplete="email"
        >
          <template #icon><IconMail size="sm" /></template>
        </AppInput>

        <div class="flex flex-col gap-3 sm:flex-row">
          <AppInput
            id="password"
            v-model="password"
            type="password"
            label="Mot de passe"
            placeholder="••••••••"
            autocomplete="new-password"
            class="flex-1"
          />
          <AppInput
            id="password2"
            v-model="passwordConfirm"
            type="password"
            label="Confirmation"
            placeholder="••••••••"
            autocomplete="new-password"
            class="flex-1"
          />
        </div>

        <label class="mb-6 flex items-start gap-2 text-sm text-gray-500">
          <input
            v-model="acceptTerms"
            type="checkbox"
            class="mt-0.5 h-4 w-4 rounded border-sup-border accent-sup-dark-green"
          />
          <span>
            J'accepte les
            <NuxtLink to="#" class="font-semibold text-sup-dark-green">
              conditions d'utilisation
            </NuxtLink>
          </span>
        </label>

        <AppButton type="submit" variant="primary" size="lg" block>Créer mon compte</AppButton>
      </form>

      <p class="mt-6 text-center text-sm text-gray-500 sm:text-base">
        Déjà un compte ?
        <NuxtLink to="/login" class="font-semibold text-sup-dark-green">Se connecter</NuxtLink>
      </p>
    </div>
  </div>
</template>
