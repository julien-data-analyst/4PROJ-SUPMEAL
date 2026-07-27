<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import IconGoogle from "~/components/icons/IconGoogle.vue";
import IconMicrosoft from "~/components/icons/IconMicrosoft.vue";
</script>

<template>
  <div class="mb-5 flex gap-2.5">
    <AppButton variant="oauth" size="lg" block>
      <template #icon><IconGoogle size="sm" /></template>
      Google
    </AppButton>
    <AppButton variant="oauth" size="lg" block>
      <template #icon><IconMicrosoft size="sm" /></template>
      Microsoft
    </AppButton>
  </div>
</template>
