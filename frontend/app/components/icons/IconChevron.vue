<script setup lang="ts">
type IconSize = "xs" | "sm" | "md" | "lg";
type Direction = "up" | "down" | "left" | "right";

const props = withDefaults(
  defineProps<{ size?: IconSize; direction?: Direction }>(),
  { size: "md", direction: "down" },
);

const sizeClasses: Record<IconSize, string> = {
  xs: "h-4 w-4",
  sm: "h-5 w-5",
  md: "h-6 w-6",
  lg: "h-7 w-7",
};

const rotationClasses: Record<Direction, string> = {
  up: "rotate-180",
  down: "rotate-0",
  left: "rotate-90",
  right: "-rotate-90",
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
    :class="[sizeClasses[props.size], rotationClasses[props.direction]]"
  >
    <polyline points="6 9 12 15 18 9" />
  </svg>
</template>
