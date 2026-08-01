<script setup lang="ts">
type ButtonVariant =
  "primary" | "secondary" | "destructive" | "ghost" | "oauth";
type ButtonSize = "sm" | "md" | "lg";

const props = withDefaults(
  defineProps<{
    variant?: ButtonVariant;
    size?: ButtonSize;
    type?: "button" | "submit" | "reset";
    disabled?: boolean;
    block?: boolean;
    to?: string;
  }>(),
  {
    variant: "primary",
    size: "md",
    type: "button",
    disabled: false,
    block: false,
    to: undefined,
  },
);

const tag = computed(() =>
  props.to ? resolveComponent("NuxtLink") : "button",
);

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "border-transparent bg-gradient-to-br from-sup-light-green to-sup-dark-green text-sup-very-gray hover:brightness-105",
  secondary:
    "border-sup-dark-green bg-sup-withe text-sup-dark-green hover:bg-sup-light-green/10",
  destructive:
    "border-transparent bg-sup-red-error text-sup-withe hover:brightness-105",
  ghost:
    "border-sup-border bg-transparent text-sup-very-gray hover:bg-sup-light-gray",
  oauth:
    "border-sup-border bg-sup-withe text-sup-very-gray hover:bg-sup-light-gray",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "px-3 py-2 text-[12px]",
  md: "px-4 py-2.5 text-[13px]",
  lg: "px-8 py-3.5 text-base",
};

const classes = computed(() => [
  variantClasses[props.variant],
  sizeClasses[props.size],
  props.block ? "w-full" : "",
]);
</script>

<template>
  <component
    :is="tag"
    :to="to"
    :type="to ? undefined : type"
    :disabled="to ? undefined : disabled"
    class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md border font-semibold transition disabled:cursor-not-allowed disabled:border-sup-light-gray disabled:bg-sup-light-gray disabled:text-gray-400 disabled:hover:brightness-100"
    :class="classes"
  >
    <span v-if="$slots.icon" class="[&>svg]:h-4 [&>svg]:w-4">
      <slot name="icon" />
    </span>
    <slot />
  </component>
</template>
