<script setup lang="ts">
type IconSize = "xs" | "sm" | "md" | "lg";

const props = withDefaults(defineProps<{ size?: IconSize }>(), { size: "md" });

const sizeClasses: Record<IconSize, string> = {
  xs: "h-4 w-4",
  sm: "h-5 w-5",
  md: "h-6 w-6",
  lg: "h-7 w-7",
};
</script>

<template>
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    :class="sizeClasses[props.size]"
  >
    <path d="M22 6l-10 7L2 6" />
    <rect x="2" y="4" width="20" height="16" rx="2" />
  </svg>
</template>
