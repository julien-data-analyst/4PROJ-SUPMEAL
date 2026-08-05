<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import IconClose from "~/components/icons/IconClose.vue";
import IconAlertTriangle from "~/components/icons/IconAlertTriangle.vue";

export interface DeleteCookbookOptions {
  keepRecipes: boolean;
  keepPlannings: boolean;
}

const props = withDefaults(
  defineProps<{
    open: boolean;
    cookbookName: string;
    recipes?: { id: number; title: string }[];
    plannings?: { id: number; name: string }[];
  }>(),
  { recipes: () => [], plannings: () => [] },
);
const emit = defineEmits<{
  close: [];
  confirm: [options: DeleteCookbookOptions];
}>();

const confirmText = ref("");
const isDeleting = ref(false);
const keepRecipes = ref(true);
const keepPlannings = ref(true);

watch(
  () => props.open,
  (open) => {
    if (open) {
      confirmText.value = "";
      keepRecipes.value = true;
      keepPlannings.value = true;
    }
  },
);

// A planning can't survive without the recipes its meals point to, so
// keeping plannings only makes sense when recipes are kept too.
watch(keepRecipes, (value) => {
  if (!value) keepPlannings.value = false;
});

const recipesToDelete = computed(() =>
  keepRecipes.value ? [] : props.recipes,
);
const planningsToDelete = computed(() =>
  keepPlannings.value ? [] : props.plannings,
);

const canConfirm = computed(
  () => confirmText.value.trim().toLowerCase() === "suppression",
);

const onConfirm = async () => {
  if (!canConfirm.value || isDeleting.value) return;
  isDeleting.value = true;
  try {
    emit("confirm", {
      keepRecipes: keepRecipes.value,
      keepPlannings: keepPlannings.value,
    });
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
        class="w-full max-w-[480px] max-h-[90vh] overflow-auto rounded-[14px] bg-sup-withe shadow-md"
      >
        <div
          class="flex items-center justify-between border-b border-sup-border px-5 py-[18px]"
        >
          <p class="text-[16px] font-semibold text-sup-very-gray">
            Supprimer le cookbook
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
              Cette action est irréversible. Le cookbook « {{ cookbookName }}
              » sera définitivement supprimé.
            </span>
          </div>

          <div
            v-if="recipes.length || plannings.length"
            class="mb-4 flex flex-col gap-2 rounded-md border border-sup-border bg-sup-light-gray p-3"
          >
            <p class="text-[12.5px] font-semibold text-sup-very-gray">
              Que faire du contenu du cookbook ?
            </p>

            <label
              class="flex items-start gap-2 text-[12.5px] text-sup-very-gray"
            >
              <input
                v-model="keepRecipes"
                type="checkbox"
                class="mt-0.5 h-4 w-4 accent-sup-dark-green"
              />
              <span>
                Garder mes recettes en personnel
                <span class="text-gray-400">({{ recipes.length }})</span>
              </span>
            </label>

            <label
              class="flex items-start gap-2 text-[12.5px] text-sup-very-gray"
            >
              <input
                v-model="keepPlannings"
                type="checkbox"
                :disabled="!keepRecipes"
                class="mt-0.5 h-4 w-4 accent-sup-dark-green disabled:opacity-50"
              />
              <span :class="!keepRecipes ? 'text-gray-400' : ''">
                Garder aussi mes plannings, avec leurs repas
                <span class="text-gray-400">({{ plannings.length }})</span>
              </span>
            </label>
            <p v-if="!keepRecipes" class="pl-6 text-[11px] text-gray-400">
              Un planning ne peut pas être gardé sans les recettes de ses repas.
            </p>
          </div>

          <div
            v-if="recipesToDelete.length"
            class="mb-3 rounded-md border border-[#F0DE9A] bg-sup-yellow-warning/15 px-[14px] py-[10px] text-[12.5px] font-medium text-[#8A6D00]"
          >
            <p>
              {{ recipesToDelete.length }} recette{{
                recipesToDelete.length > 1 ? "s" : ""
              }}
              définitivement supprimée{{
                recipesToDelete.length > 1 ? "s" : ""
              }}
              :
            </p>
            <ul class="mt-1.5 flex flex-wrap gap-1.5">
              <li
                v-for="recipe in recipesToDelete"
                :key="recipe.id"
                class="rounded-full bg-sup-withe px-2.5 py-0.5 text-[11px] font-semibold"
              >
                {{ recipe.title }}
              </li>
            </ul>
          </div>

          <div
            v-if="planningsToDelete.length"
            class="mb-3 rounded-md border border-[#F0DE9A] bg-sup-yellow-warning/15 px-[14px] py-[10px] text-[12.5px] font-medium text-[#8A6D00]"
          >
            <p>
              {{ planningsToDelete.length }} planning{{
                planningsToDelete.length > 1 ? "s" : ""
              }}
              définitivement supprimé{{
                planningsToDelete.length > 1 ? "s" : ""
              }}
              :
            </p>
            <ul class="mt-1.5 flex flex-wrap gap-1.5">
              <li
                v-for="planning in planningsToDelete"
                :key="planning.id"
                class="rounded-full bg-sup-withe px-2.5 py-0.5 text-[11px] font-semibold"
              >
                {{ planning.name }}
              </li>
            </ul>
          </div>

          <p
            v-if="
              (keepRecipes && recipes.length) ||
              (keepPlannings && plannings.length)
            "
            class="mb-3 text-[12px] text-gray-500"
          >
            Le reste redeviendra personnel (retiré du cookbook, pas supprimé).
          </p>

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
            {{ isDeleting ? "Suppression..." : "Supprimer le cookbook" }}
          </AppButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>
