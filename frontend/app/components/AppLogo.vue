<script setup lang="ts">
withDefaults(
  defineProps<{
    tagline?: string;
    size?: "sm" | "md" | "lg";
  }>(),
  {
    size: "md",
  },
);

const sizeClasses: Record<string, string> = {
  sm: "h-8",
  md: "h-11",
  lg: "h-16",
};
</script>

<template>
  <div class="flex flex-col items-center gap-3">
    <img
      src="/Logo%20entreprise.png"
      alt="SUPMEAL"
      class="w-auto"
      :class="sizeClasses[size]"
    />
    <p v-if="tagline" class="text-center text-[13px] text-gray-500">
      {{ tagline }}
    </p>
  </div>
</template>
