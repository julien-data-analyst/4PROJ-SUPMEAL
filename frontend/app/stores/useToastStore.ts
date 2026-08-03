// stores/useToastStore.ts
import { defineStore } from "pinia";

export type ToastType = "success" | "warning" | "error";

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

let nextId = 0;

export const useToastStore = defineStore("toast", () => {
  const toasts = ref<Toast[]>([]);

  const remove = (id: string) => {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  };

  const push = (type: ToastType, message: string, durationMs = 4500) => {
    const id = `toast-${++nextId}`;
    toasts.value = [...toasts.value, { id, type, message }];
    if (import.meta.client) {
      setTimeout(() => remove(id), durationMs);
    }
    return id;
  };

  const success = (message: string) => push("success", message);
  const warning = (message: string) => push("warning", message);
  const error = (message: string) => push("error", message);

  return { toasts, push, success, warning, error, remove };
});
