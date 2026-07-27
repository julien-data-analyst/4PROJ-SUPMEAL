<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue?: string;
    id: string;
    label?: string;
    type?: string;
    placeholder?: string;
    autocomplete?: string;
    hint?: string;
    error?: string;
  }>(),
  {
    modelValue: "",
    type: "text",
  },
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const showPassword = ref(false);
const isPassword = computed(() => props.type === "password");
const inputType = computed(() =>
  isPassword.value ? (showPassword.value ? "text" : "password") : props.type,
);
</script>

<template>
  <div class="mb-4 flex flex-col gap-1.5">
    <label v-if="label" :for="id" class="text-[12.5px] font-semibold text-sup-very-gray">
      {{ label }}
    </label>

    <div class="relative">
      <span
        v-if="$slots.icon"
        class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 [&>svg]:h-4 [&>svg]:w-4"
      >
        <slot name="icon" />
      </span>

      <input
        :id="id"
        :type="inputType"
        :value="modelValue"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        class="w-full rounded-md border bg-sup-withe px-3 py-2.5 text-[13.5px] text-sup-very-gray placeholder:text-gray-400 focus:outline-none focus:ring-2"
        :class="[
          $slots.icon ? 'pl-9' : '',
          isPassword ? 'pr-10' : '',
          error
            ? 'border-sup-red-error focus:border-sup-red-error focus:ring-sup-red-error/20'
            : 'border-sup-border focus:border-sup-dark-green focus:ring-sup-light-green/30',
        ]"
        @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />

      <button
        v-if="isPassword"
        type="button"
        class="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-sup-very-gray"
        :aria-label="showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'"
        @click="showPassword = !showPassword"
      >
        <svg
          v-if="!showPassword"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="h-4 w-4"
        >
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
        <svg
          v-else
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="h-4 w-4"
        >
          <path
            d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a18.6 18.6 0 0 1 5.06-5.94M9.9 4.24A9.1 9.1 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.24-1.34a3 3 0 1 1-4.24-4.24"
          />
          <path d="M1 1l22 22" />
        </svg>
      </button>
    </div>

    <p v-if="error" class="text-[11.5px] text-sup-red-error">{{ error }}</p>
    <p v-else-if="hint" class="text-[11.5px] text-gray-400">{{ hint }}</p>
  </div>
</template>
