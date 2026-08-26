<script setup lang="ts">
import IconEye from "~/components/icons/IconEye.vue";
import IconEyeOff from "~/components/icons/IconEyeOff.vue";

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
  <div class="mb-5 flex flex-col gap-2">
    <label
      v-if="label"
      :for="id"
      class="text-sm font-semibold text-sup-very-gray sm:text-base"
    >
      {{ label }}
    </label>

    <div class="relative">
      <span
        v-if="$slots.icon"
        class="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 [&>svg]:h-5 [&>svg]:w-5"
      >
        <slot name="icon" />
      </span>

      <input
        :id="id"
        :type="inputType"
        :value="modelValue"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        class="w-full rounded-md border bg-sup-withe px-4 py-3 text-base text-sup-very-gray placeholder:text-gray-400 focus:outline-none focus:ring-2 sm:py-3.5"
        :class="[
          $slots.icon ? 'pl-11' : '',
          isPassword ? 'pr-12' : '',
          error
            ? 'border-sup-red-error focus:border-sup-red-error focus:ring-sup-red-error/20'
            : 'border-sup-border focus:border-sup-dark-green focus:ring-sup-light-green/30',
        ]"
        @input="
          emit('update:modelValue', ($event.target as HTMLInputElement).value)
        "
      />

      <button
        v-if="isPassword"
        type="button"
        class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-sup-very-gray"
        :aria-label="
          showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'
        "
        @click="showPassword = !showPassword"
      >
        <IconEye v-if="!showPassword" size="sm" />
        <IconEyeOff v-else size="sm" />
      </button>
    </div>

    <p v-if="error" class="text-sm text-sup-red-error">{{ error }}</p>
    <p v-else-if="hint" class="text-sm text-gray-400">{{ hint }}</p>
  </div>
</template>
