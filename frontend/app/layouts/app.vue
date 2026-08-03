<script setup lang="ts">
import AppSidebar from "~/components/layout/AppSidebar.vue";
</script>

<template>
  <div
    class="flex min-h-screen bg-sup-light-gray text-[14px] text-sup-very-gray"
  >
    <AppSidebar />
    <main class="min-w-0 flex-1 px-8 pb-[60px] pt-[26px]">
      <slot />
    </main>
  </div>
</template>
