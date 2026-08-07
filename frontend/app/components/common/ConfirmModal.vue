<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import IconClose from "~/components/icons/IconClose.vue";
import IconAlertTriangle from "~/components/icons/IconAlertTriangle.vue";

const props = withDefaults(
  defineProps<{
    open: boolean;
    title: string;
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
    variant?: "default" | "destructive";
    typedWord?: string;
    // Label of a confirmation checkbox the user must tick before the confirm
    // button unlocks - an alternative gate to `typedWord` for actions that
    // just need acknowledgement rather than a typed match (e.g. exporting
    // data in a raw, unencrypted format).
    checkboxLabel?: string;
  }>(),
  {
    confirmLabel: "Confirmer",
    cancelLabel: "Annuler",
    variant: "default",
    typedWord: undefined,
    checkboxLabel: undefined,
  },
);
const emit = defineEmits<{ close: []; confirm: [] }>();

const confirmText = ref("");
const checkboxChecked = ref(false);
const isConfirming = ref(false);

watch(
  () => props.open,
  (open) => {
    if (open) {
      confirmText.value = "";
      checkboxChecked.value = false;
    }
  },
);

const canConfirm = computed(
  () =>
    (!props.typedWord ||
      confirmText.value.trim().toLowerCase() ===
        props.typedWord.toLowerCase()) &&
    (!props.checkboxLabel || checkboxChecked.value),
);

const onConfirm = async () => {
  if (!canConfirm.value || isConfirming.value) return;
  isConfirming.value = true;
  try {
    emit("confirm");
  } finally {
    isConfirming.value = false;
  }
};
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-5"
      @click.self="emit('close')"
    >
      <div
        class="max-h-[90vh] w-full max-w-[460px] overflow-auto rounded-[14px] bg-sup-withe shadow-md"
      >
        <div
          class="flex items-center justify-between border-b border-sup-border px-5 py-[18px]"
        >
          <p class="text-[16px] font-semibold text-sup-very-gray">
            {{ title }}
          </p>
          <button
            type="button"
            class="text-gray-400 hover:text-sup-very-gray"
            @click="emit('close')"
          >
            <IconClose size="sm" />
          </button>
        </div>

        <div class="p-5">
          <div
            v-if="variant === 'destructive'"
            class="mb-4 flex items-center gap-2 rounded-md border border-red-200 bg-sup-red-error/10 px-[14px] py-[10px] text-[12.5px] font-medium text-sup-red-error"
          >
            <IconAlertTriangle size="xs" class="shrink-0" />
            <span>{{ message }}</span>
          </div>
          <p v-else class="text-[13.5px] text-sup-very-gray">{{ message }}</p>

          <div v-if="typedWord" class="mt-[14px]">
            <p class="mb-2 text-[12px] text-gray-500">
              Pour confirmer, tapez <strong>{{ typedWord }}</strong> ci-dessous
              :
            </p>
            <input
              v-model="confirmText"
              type="text"
              :placeholder="typedWord"
              class="w-full rounded-md border border-sup-border bg-sup-withe px-3 py-[9px] text-[13.5px] text-sup-very-gray focus:border-sup-red-error focus:outline-none focus:ring-2 focus:ring-sup-red-error/20"
              @keyup.enter="onConfirm"
            />
          </div>

          <label
            v-if="checkboxLabel"
            class="mt-[14px] flex items-start gap-2 text-[12.5px] text-sup-very-gray"
          >
            <input
              v-model="checkboxChecked"
              type="checkbox"
              class="mt-0.5 h-4 w-4 rounded border-sup-border accent-sup-dark-green"
            />
            <span>{{ checkboxLabel }}</span>
          </label>
        </div>

        <div
          class="flex justify-end gap-[10px] border-t border-sup-border px-5 py-4"
        >
          <AppButton variant="ghost" @click="emit('close')">
            {{ cancelLabel }}
          </AppButton>
          <AppButton
            :variant="variant === 'destructive' ? 'destructive' : 'primary'"
            :disabled="!canConfirm || isConfirming"
            @click="onConfirm"
          >
            {{ confirmLabel }}
          </AppButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>
