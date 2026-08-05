<script setup lang="ts">
import type { IngredientLine } from "~/composables/useRecipes";
import { fileToDataUrl } from "~/composables/useRecipes";
import { useRecipeStore } from "~/stores/useRecipeStore";
import type { Ingredient } from "~/stores/useRecipeStore";
import IconCamera from "~/components/icons/IconCamera.vue";
import IconTrash from "~/components/icons/IconTrash.vue";
import IconAlertTriangle from "~/components/icons/IconAlertTriangle.vue";

const props = defineProps<{
  isDuplicate?: boolean;
  excludeIngredientIds?: number[];
}>();

const line = defineModel<IngredientLine>({ required: true });
const emit = defineEmits<{ remove: [] }>();

const store = useRecipeStore();
const suggestions = ref<Ingredient[]>([]);
const showSuggestions = ref(false);
let searchHandle: ReturnType<typeof setTimeout> | undefined;

const isNewIngredient = computed(
  () => !line.value.ingredientId && line.value.name.trim().length > 0,
);

// Already-used-elsewhere ingredients are hidden from the picker so the same
// catalogue ingredient can't be selected on two lines at once.
const visibleSuggestions = computed(() =>
  suggestions.value.filter(
    (s) => !(props.excludeIngredientIds ?? []).includes(s.id),
  ),
);

const onNameInput = () => {
  line.value.ingredientId = null;
  line.value.image = null;
  showSuggestions.value = true;
  if (searchHandle) clearTimeout(searchHandle);
  const query = line.value.name.trim();
  if (!query) {
    suggestions.value = [];
    return;
  }
  searchHandle = setTimeout(async () => {
    suggestions.value = await store.fetchIngredients(query);
  }, 250);
};

const selectSuggestion = (ingredient: Ingredient) => {
  line.value.ingredientId = ingredient.id;
  line.value.name = ingredient.name;
  line.value.image = ingredient.image;
  showSuggestions.value = false;
};

const onNameBlur = () => {
  setTimeout(() => {
    showSuggestions.value = false;
  }, 150);
};

const onImageChange = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  line.value.image = await fileToDataUrl(file);
};

const inputClasses =
  "w-full rounded-md border border-sup-border bg-sup-withe px-3 py-[9px] text-[13.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30";
const numberInputClasses =
  "w-full rounded-md border border-sup-border bg-sup-withe px-2 py-[9px] text-[13.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30";
const numberLabelClasses =
  "mb-1 block text-[10px] font-semibold uppercase tracking-wide text-gray-400";
</script>

<template>
  <div
    class="rounded-md border p-3"
    :class="isDuplicate ? 'border-sup-red-error' : 'border-sup-border'"
  >
    <div class="relative mb-3">
      <input
        v-model="line.name"
        type="text"
        placeholder="Nom de l'ingrédient"
        :class="inputClasses"
        @input="onNameInput"
        @focus="showSuggestions = true"
        @blur="onNameBlur"
      />
      <ul
        v-if="showSuggestions && visibleSuggestions.length"
        class="absolute z-10 mt-1 max-h-40 w-full overflow-y-auto rounded-md border border-sup-border bg-sup-withe shadow-lg"
      >
        <li v-for="s in visibleSuggestions" :key="s.id">
          <button
            type="button"
            class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-sup-very-gray hover:bg-sup-light-gray"
            @mousedown.prevent="selectSuggestion(s)"
          >
            <img
              v-if="s.image"
              :src="s.image"
              class="h-5 w-5 rounded object-cover"
            />
            {{ s.name }}
          </button>
        </li>
      </ul>
    </div>

    <div
      v-if="isDuplicate"
      class="mb-2 flex items-center gap-1.5 text-[11px] font-medium text-sup-red-error"
    >
      <IconAlertTriangle size="xs" />
      Cet ingrédient est déjà dans la liste.
    </div>

    <div class="grid grid-cols-3 gap-3">
      <div>
        <label :class="numberLabelClasses">Quantité</label>
        <input
          v-model="line.quantity"
          type="number"
          step="0.01"
          min="0"
          placeholder="0"
          :class="numberInputClasses"
        />
      </div>
      <div>
        <label :class="numberLabelClasses">Unité</label>
        <input
          v-model="line.unity"
          type="text"
          placeholder="g, ml..."
          :class="numberInputClasses"
        />
      </div>
      <div>
        <label :class="numberLabelClasses">Personnes</label>
        <input
          v-model="line.personNumbers"
          type="number"
          min="1"
          placeholder="4"
          :class="numberInputClasses"
        />
      </div>
    </div>

    <div
      v-if="isNewIngredient"
      class="mt-2 flex items-center gap-2 rounded-md bg-sup-yellow-warning/10 p-2 text-xs text-sup-very-gray"
    >
      <IconCamera size="xs" />
      <span class="flex-1">Nouvel ingrédient : une image est obligatoire.</span>
    </div>

    <div class="mt-2 flex items-center gap-2">
      <img
        v-if="line.image"
        :src="line.image"
        class="h-10 w-10 rounded border border-sup-border object-cover"
      />
      <label
        class="cursor-pointer text-xs font-semibold text-sup-dark-green hover:underline"
      >
        {{ line.image ? "Changer l'image" : "Choisir une image" }}
        <input
          type="file"
          accept="image/*"
          class="hidden"
          @change="onImageChange"
        />
      </label>
    </div>

    <button
      type="button"
      class="mt-3 flex items-center gap-1 text-xs font-medium text-sup-red-error hover:underline"
      @click="emit('remove')"
    >
      <IconTrash size="xs" />
      Retirer
    </button>
  </div>
</template>
