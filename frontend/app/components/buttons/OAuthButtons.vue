<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import IconGoogle from "~/components/icons/IconGoogle.vue";
import IconMicrosoft from "~/components/icons/IconMicrosoft.vue";
import { useOAuth } from "~/composables/useOAuth";

const { startOAuth } = useOAuth();

const error = ref("");

const onMicrosoftLogin = () => {
  error.value = "";
  try {
    startOAuth("microsoft");
  } catch (cause) {
    error.value =
      cause instanceof Error
        ? cause.message
        : "Connexion Microsoft impossible.";
  }
};
</script>

<template>
  <div>
    <div class="mb-5 flex gap-2.5">
      <AppButton
        variant="oauth"
        size="lg"
        block
        disabled
        title="Bientôt disponible"
      >
        <template #icon><IconGoogle size="sm" /></template>
        Google
      </AppButton>
      <AppButton variant="oauth" size="lg" block @click="onMicrosoftLogin">
        <template #icon><IconMicrosoft size="sm" /></template>
        Microsoft
      </AppButton>
    </div>
    <p v-if="error" class="-mt-3 mb-5 text-sm text-sup-red-error">
      {{ error }}
    </p>
  </div>
</template>
