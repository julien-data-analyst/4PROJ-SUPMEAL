<script setup lang="ts">
import AppLogo from "~/components/AppLogo.vue";
import AppInput from "~/components/forms/AppInput.vue";
import AppButton from "~/components/buttons/AppButton.vue";
import OAuthButtons from "~/components/buttons/OAuthButtons.vue";
import IconMail from "~/components/icons/IconMail.vue";
import { useAuth } from "~/composables/useAuth";
import { loginSchema } from "~/composables/auth";
import { useFormValidation } from "~/composables/managingUser/useZodForm";

definePageMeta({ layout: false });

const { login } = useAuth();
const { form, errors, validate } = useFormValidation(loginSchema, {
  email: "",
  password: "",
});

const rememberMe = ref(false);
const isSubmitting = ref(false);
const submitError = ref("");

const onSubmit = async () => {
  submitError.value = "";

  if (!validate()) return;

  isSubmitting.value = true;
  try {
    await login({ email: form.email ?? "", password: form.password ?? "" });
    await navigateTo("/home");
  } catch {
    submitError.value = "Adresse email ou mot de passe incorrect.";
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<template>
  <div
    class="flex min-h-screen items-center justify-center bg-gradient-to-br from-sup-light-green/10 via-sup-light-gray to-sup-light-gray px-6 py-10"
  >
    <div
      class="w-full max-w-md rounded-2xl border border-sup-border bg-sup-withe p-8 shadow-lg sm:max-w-lg sm:p-10 lg:max-w-xl lg:p-12"
    >
      <AppLogo
        size="lg"
        tagline="Vos recettes, cookbooks & plannings au même endroit"
      />

      <h1
        class="mt-8 text-center text-2xl font-bold text-sup-very-gray sm:text-3xl"
      >
        Connexion
      </h1>
      <p class="mb-8 mt-2 text-center text-sm text-gray-500 sm:text-base">
        Content de vous revoir sur SUPMEAL
      </p>

      <OAuthButtons />

      <div class="mb-6 flex items-center gap-3">
        <div class="h-px flex-1 bg-sup-border" />
        <span class="text-xs font-medium text-gray-400 sm:text-sm"
          >OU PAR EMAIL</span
        >
        <div class="h-px flex-1 bg-sup-border" />
      </div>

      <form @submit.prevent="onSubmit">
        <AppInput
          id="email"
          v-model="form.email"
          type="email"
          label="Adresse email"
          placeholder="john.doe@email.com"
          autocomplete="email"
          :error="errors.email"
        >
          <template #icon><IconMail size="sm" /></template>
        </AppInput>

        <AppInput
          id="password"
          v-model="form.password"
          type="password"
          label="Mot de passe"
          placeholder="••••••••"
          autocomplete="current-password"
          :error="errors.password"
        />

        <div class="mb-6 flex items-center justify-between">
          <label class="flex items-center gap-2 text-sm text-gray-500">
            <input
              v-model="rememberMe"
              type="checkbox"
              class="h-4 w-4 rounded border-sup-border accent-sup-dark-green"
            />
            Se souvenir de moi
          </label>
          <NuxtLink to="#" class="text-sm font-semibold text-sup-dark-green">
            Mot de passe oublié ?
          </NuxtLink>
        </div>

        <p v-if="submitError" class="mb-4 text-sm text-sup-red-error">
          {{ submitError }}
        </p>

        <AppButton
          type="submit"
          variant="primary"
          size="lg"
          block
          :disabled="isSubmitting"
        >
          {{ isSubmitting ? "Connexion..." : "Se connecter" }}
        </AppButton>
      </form>

      <p class="mt-6 text-center text-sm text-gray-500 sm:text-base">
        Pas encore de compte ?
        <NuxtLink to="/register" class="font-semibold text-sup-dark-green">
          Créer un compte
        </NuxtLink>
      </p>
    </div>
  </div>
</template>
