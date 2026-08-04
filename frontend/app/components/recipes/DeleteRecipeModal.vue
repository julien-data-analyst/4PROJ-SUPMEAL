<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import IconClose from "~/components/icons/IconClose.vue";
import IconAlertTriangle from "~/components/icons/IconAlertTriangle.vue";
import IconCalendar from "~/components/icons/IconCalendar.vue";
import type { PlanningUsage } from "~/stores/useRecipeStore";

const props = withDefaults(
  defineProps<{
    open: boolean;
    recipeTitle: string;
    usedInPlannings?: PlanningUsage[];
  }>(),
  { usedInPlannings: () => [] },
);
const emit = defineEmits<{ close: []; confirm: [] }>();

const confirmText = ref("");
const isDeleting = ref(false);

watch(
  () => props.open,
  (open) => {
    if (open) confirmText.value = "";
  },
);

const canConfirm = computed(
  () => confirmText.value.trim().toLowerCase() === "suppression",
);

const onConfirm = async () => {
  if (!canConfirm.value || isDeleting.value) return;
  isDeleting.value = true;
  try {
    emit("confirm");
  } finally {
    isDeleting.value = false;
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
        class="w-full max-w-[460px] max-h-[90vh] overflow-auto rounded-[14px] bg-sup-withe shadow-md"
      >
        <div
          class="flex items-center justify-between border-b border-sup-border px-5 py-[18px]"
        >
          <p class="text-[16px] font-semibold text-sup-very-gray">
            Supprimer la recette
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
            class="mb-4 flex items-center gap-2 rounded-md border border-red-200 bg-sup-red-error/10 px-[14px] py-[10px] text-[12.5px] font-medium text-sup-red-error"
          >
            <IconAlertTriangle size="xs" class="shrink-0" />
            <span>
              Cette action est irréversible. La recette « {{ recipeTitle }} »
              sera définitivement supprimée.
            </span>
          </div>

          <div
            v-if="usedInPlannings.length"
            class="mb-4 rounded-md border border-[#F0DE9A] bg-sup-yellow-warning/15 px-[14px] py-[10px] text-[12.5px] font-medium text-[#8A6D00]"
          >
            <div class="flex items-center gap-2">
              <IconCalendar size="xs" class="shrink-0" />
              <span>
                Utilisée dans {{ usedInPlannings.length }} planning{{
                  usedInPlannings.length > 1 ? "s" : ""
                }}
                : elle en sera retirée.
              </span>
            </div>
            <ul class="mt-1.5 flex flex-wrap gap-1.5 pl-6">
              <li
                v-for="planning in usedInPlannings"
                :key="planning.id"
                class="rounded-full bg-sup-withe px-2.5 py-0.5 text-[11px] font-semibold"
              >
                {{ planning.name }}
              </li>
            </ul>
          </div>

          <div class="my-[14px]">
            <p class="mb-2 text-[12px] text-gray-500">
              Pour confirmer, tapez <strong>suppression</strong> ci-dessous :
            </p>
            <input
              v-model="confirmText"
              type="text"
              placeholder="suppression"
              class="w-full rounded-md border border-sup-border bg-sup-withe px-3 py-[9px] text-[13.5px] text-sup-very-gray focus:border-sup-red-error focus:outline-none focus:ring-2 focus:ring-sup-red-error/20"
              @keyup.enter="onConfirm"
            />
          </div>
        </div>

        <div
          class="flex justify-end gap-[10px] border-t border-sup-border px-5 py-4"
        >
          <AppButton variant="ghost" @click="emit('close')">
            Annuler
          </AppButton>
          <AppButton
            variant="destructive"
            :disabled="!canConfirm || isDeleting"
            @click="onConfirm"
          >
            {{ isDeleting ? "Suppression..." : "Supprimer la recette" }}
          </AppButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>
