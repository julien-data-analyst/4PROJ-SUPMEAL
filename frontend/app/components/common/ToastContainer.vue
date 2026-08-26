<script setup lang="ts">
import IconCheck from "~/components/icons/IconCheck.vue";
import IconAlertTriangle from "~/components/icons/IconAlertTriangle.vue";
import IconClose from "~/components/icons/IconClose.vue";
import { useToastStore, type ToastType } from "~/stores/useToastStore";

const store = useToastStore();

const variantClasses: Record<ToastType, string> = {
  success: "border-sup-dark-green/30 bg-sup-light-green/15 text-sup-dark-green",
  warning: "border-[#F0DE9A] bg-sup-yellow-warning/15 text-[#8A6D00]",
  error: "border-red-200 bg-sup-red-error/10 text-sup-red-error",
};
</script>

<template>
  <Teleport to="body">
    <div class="fixed bottom-5 right-5 z-[60] flex w-[320px] flex-col gap-2">
      <TransitionGroup
        enter-active-class="transition duration-150 ease-out"
        enter-from-class="opacity-0 translate-y-1"
        leave-active-class="transition duration-150 ease-in"
        leave-to-class="opacity-0"
      >
        <div
          v-for="toast in store.toasts"
          :key="toast.id"
          class="flex items-start gap-2 rounded-md border px-[14px] py-[10px] text-[13px] font-medium shadow-md"
          :class="variantClasses[toast.type]"
        >
          <IconCheck
            v-if="toast.type === 'success'"
            size="xs"
            class="mt-0.5 shrink-0"
          />
          <IconAlertTriangle v-else size="xs" class="mt-0.5 shrink-0" />
          <span class="flex-1">{{ toast.message }}</span>
          <button
            type="button"
            class="shrink-0 opacity-60 hover:opacity-100"
            :aria-label="'Fermer la notification'"
            @click="store.remove(toast.id)"
          >
            <IconClose size="xs" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>
