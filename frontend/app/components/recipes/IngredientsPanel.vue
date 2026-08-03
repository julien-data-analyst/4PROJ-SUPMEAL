<script setup lang="ts">
import type { IngredientLine } from "~/composables/useRecipes";
import { emptyIngredientLine } from "~/composables/useRecipes";
import IngredientRow from "~/components/recipes/IngredientRow.vue";
import IconPlus from "~/components/icons/IconPlus.vue";

const lines = defineModel<IngredientLine[]>({ required: true });

const defaultPersons = ref("4");

const addLine = () => {
  lines.value = [...lines.value, emptyIngredientLine(defaultPersons.value)];
};

const removeLine = (key: string) => {
  lines.value = lines.value.filter((l) => l.key !== key);
};

// A line is a duplicate if another line shares its (trimmed, case-insensitive)
// name - covers both "same catalogue ingredient picked twice" and "same new
// ingredient name typed twice".
const isDuplicate = (line: IngredientLine): boolean => {
  const name = line.name.trim().toLowerCase();
  if (!name) return false;
  return lines.value.some(
    (l) => l.key !== line.key && l.name.trim().toLowerCase() === name,
  );
};

const excludeIngredientIds = (line: IngredientLine): number[] =>
  lines.value
    .filter((l) => l.key !== line.key && l.ingredientId !== null)
    .map((l) => l.ingredientId as number);
</script>

<template>
  <div
    class="rounded-[14px] border border-sup-border bg-sup-withe p-[18px] shadow-sm"
  >
    <div class="mb-3 flex items-center justify-between gap-2">
      <p class="text-[14.5px] font-bold text-sup-very-gray">Ingrédients</p>
      <label class="flex items-center gap-1.5 text-[11px] text-gray-400">
        Portion
        <input
          v-model="defaultPersons"
          type="number"
          min="1"
          class="w-11 rounded-md border border-sup-border bg-sup-withe px-1.5 py-1 text-[12px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none"
        />
        pers.
      </label>
    </div>

    <div class="flex flex-col gap-3">
      <IngredientRow
        v-for="line in lines"
        :key="line.key"
        :model-value="line"
        :is-duplicate="isDuplicate(line)"
        :exclude-ingredient-ids="excludeIngredientIds(line)"
        @update:model-value="
          (v) => (lines = lines.map((l) => (l.key === line.key ? v : l)))
        "
        @remove="removeLine(line.key)"
      />
    </div>

    <button
      type="button"
      class="mt-3 flex w-full items-center justify-center gap-2 rounded-md border border-dashed border-sup-border py-[9px] text-[13px] font-medium text-sup-dark-green hover:bg-sup-light-green/10"
      @click="addLine"
    >
      <IconPlus size="xs" />
      Ajouter un ingrédient
    </button>
  </div>
</template>
