<script setup lang="ts">
import type { Recipe } from "~/stores/useRecipeStore";
import { useRecipes } from "~/composables/useRecipes";
import type { RecipePick } from "~/composables/usePlanningEditView";
import IconClose from "~/components/icons/IconClose.vue";
import IconRecipe from "~/components/icons/IconRecipe.vue";

const props = withDefaults(
  defineProps<{ expanded?: boolean; recipes?: Recipe[] }>(),
  { expanded: false, recipes: undefined },
);

const pick = defineModel<RecipePick>({ required: true });

const { searchMyRecipes } = useRecipes();

const suggestions = ref<Recipe[]>([]);
const showSuggestions = ref(false);
let searchHandle: ReturnType<typeof setTimeout> | undefined;

// When `recipes` is provided (a cookbook-scoped planning), suggestions are
// filtered client-side from that fixed list instead of searching the
// caller's personal recipes on the server.
const filterLocal = (query: string): Recipe[] => {
  const list = props.recipes ?? [];
  const q = query.trim().toLowerCase();
  const matches = q ? list.filter((r) => r.title.toLowerCase().includes(q)) : list;
  return matches.slice(0, 8);
};

const onInput = () => {
  pick.value = { ...pick.value, id: null, image: null };
  showSuggestions.value = true;
  const query = pick.value.title.trim();
  if (props.recipes) {
    suggestions.value = filterLocal(query);
    return;
  }
  if (searchHandle) clearTimeout(searchHandle);
  if (!query) {
    suggestions.value = [];
    return;
  }
  searchHandle = setTimeout(async () => {
    suggestions.value = await searchMyRecipes(query);
  }, 250);
};

const onFocus = async () => {
  showSuggestions.value = true;
  if (props.recipes) {
    if (!suggestions.value.length) suggestions.value = filterLocal(pick.value.title);
    return;
  }
  if (!pick.value.title.trim() && !suggestions.value.length) {
    suggestions.value = await searchMyRecipes("");
  }
};

const onBlur = () => {
  setTimeout(() => {
    showSuggestions.value = false;
  }, 150);
};

const select = (recipe: Recipe) => {
  pick.value = { id: recipe.id, title: recipe.title, image: recipe.image };
  showSuggestions.value = false;
};

const clear = () => {
  pick.value = { id: null, title: "", image: null };
  suggestions.value = [];
};
</script>

<template>
  <div class="relative">
    <div
      class="flex items-center gap-1.5 rounded-md border border-sup-border bg-sup-withe pr-1 transition-[padding]"
      :class="expanded ? 'gap-2 pl-2 py-1.5' : 'pl-1.5 py-1'"
    >
      <div
        class="flex shrink-0 items-center justify-center overflow-hidden rounded bg-sup-light-gray text-gray-400 transition-[width,height]"
        :class="expanded ? 'h-9 w-9' : 'h-6 w-6'"
      >
        <img
          v-if="pick.image"
          :src="pick.image"
          class="h-full w-full object-cover"
        />
        <IconRecipe v-else :size="expanded ? 'sm' : 'xs'" />
      </div>
      <input
        v-model="pick.title"
        type="text"
        placeholder="Recette..."
        :title="pick.title || undefined"
        class="w-full min-w-0 border-none bg-transparent text-sup-very-gray outline-none placeholder:text-gray-400"
        :class="expanded ? 'text-[13.5px]' : 'text-[12px]'"
        @input="onInput"
        @focus="onFocus"
        @blur="onBlur"
      />
      <button
        v-if="pick.id || pick.title"
        type="button"
        class="shrink-0 text-gray-400 hover:text-sup-red-error"
        title="Retirer"
        @mousedown.prevent="clear"
      >
        <IconClose size="xs" />
      </button>
    </div>

    <ul
      v-if="showSuggestions && suggestions.length"
      class="absolute left-0 top-full z-20 mt-1 max-h-56 w-full min-w-[220px] overflow-y-auto rounded-md border border-sup-border bg-sup-withe shadow-lg"
    >
      <li v-for="recipe in suggestions" :key="recipe.id">
        <button
          type="button"
          :title="recipe.title"
          class="flex w-full items-center gap-2 px-3 py-2 text-left text-[12.5px] text-sup-very-gray hover:bg-sup-light-gray"
          @mousedown.prevent="select(recipe)"
        >
          <img
            v-if="recipe.image"
            :src="recipe.image"
            class="h-6 w-6 shrink-0 rounded object-cover"
          />
          <IconRecipe v-else size="xs" class="shrink-0 text-gray-400" />
          <span class="truncate">{{ recipe.title }}</span>
        </button>
      </li>
    </ul>
    <p
      v-else-if="showSuggestions && pick.title.trim()"
      class="absolute left-0 top-full z-20 mt-1 w-full min-w-[220px] rounded-md border border-sup-border bg-sup-withe px-3 py-2 text-[12px] text-gray-400 shadow-lg"
    >
      {{ recipes ? "Aucune recette dans ce cookbook." : "Aucune recette personnelle trouvée." }}
    </p>
  </div>
</template>
