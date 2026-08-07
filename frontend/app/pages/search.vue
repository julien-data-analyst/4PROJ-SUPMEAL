<script setup lang="ts">
import SearchFilters from "~/components/search/SearchFilters.vue";
import RecipeSearchResults from "~/components/search/RecipeSearchResults.vue";
import PlanningSearchResults from "~/components/search/PlanningSearchResults.vue";
import CookbookSearchResults from "~/components/search/CookbookSearchResults.vue";
import IconRecipe from "~/components/icons/IconRecipe.vue";
import IconCalendar from "~/components/icons/IconCalendar.vue";
import IconCookbook from "~/components/icons/IconCookbook.vue";
import IconSearch from "~/components/icons/IconSearch.vue";
import IconTag from "~/components/icons/IconTag.vue";
import IconStar from "~/components/icons/IconStar.vue";
import { useRecipeStore } from "~/stores/useRecipeStore";
import { useCuisinePreferences } from "~/composables/useCuisinePreferences";
import { sumStepMinutes, capitalizeFirst } from "~/composables/useRecipes";
import { usePlanningStore } from "~/stores/usePlanningStore";
import { useCookbookStore } from "~/stores/cookbooks/useCookbookStore";
import {
  type SearchType,
  createRecipeFilters,
  createPlanningFilters,
  createCookbookFilters,
} from "~/composables/useSearch";

definePageMeta({ layout: "app" });

const searchTypes: { key: SearchType; label: string; icon: object }[] = [
  { key: "recipes", label: "Recettes", icon: IconRecipe },
  { key: "plannings", label: "Plannings", icon: IconCalendar },
  { key: "cookbooks", label: "Cookbooks", icon: IconCookbook },
];

const searchType = ref<SearchType>("recipes");

const recipeFilters = ref(createRecipeFilters());
const planningFilters = ref(createPlanningFilters());
const cookbookFilters = ref(createCookbookFilters());

const { preferences: cuisinePreferences } = useCuisinePreferences();

// Applies the tags saved in Settings > Préférences culinaires as the
// recipe-tags filter in one click, instead of typing/browsing them again.
const applyCuisinePreferences = () => {
  searchType.value = "recipes";
  recipeFilters.value.tags = cuisinePreferences.value.join(", ");
  runSearch();
};

const recipeStore = useRecipeStore();
const planningStore = usePlanningStore();
const cookbookStore = useCookbookStore();

// Quick, frontend-only refinement over whatever the current search already
// loaded - narrows the visible cards on every keystroke without another API
// call. Reset whenever the search type or an actual (backend) search changes.
const quickFilter = ref("");
const isLoading = ref(true);

const PAGE_SIZE = 48;

const runSearch = async () => {
  isLoading.value = true;
  quickFilter.value = "";
  try {
    if (searchType.value === "recipes") {
      const f = recipeFilters.value;
      await recipeStore.fetchRecipes({
        name: f.name || undefined,
        ingredients: f.ingredients || undefined,
        tags: f.tags || undefined,
        cookbook:
          f.cookbookScope === "cookbook"
            ? f.cookbookName || undefined
            : undefined,
        in_cookbook:
          f.cookbookScope === "all"
            ? undefined
            : f.cookbookScope === "cookbook",
        planning:
          f.planningScope === "planned"
            ? f.planningName || undefined
            : undefined,
        in_planning:
          f.planningScope === "all" ? undefined : f.planningScope === "planned",
        favorite:
          f.favoriteScope === "all"
            ? undefined
            : f.favoriteScope === "favorite",
        page_size: PAGE_SIZE,
      });
    } else if (searchType.value === "plannings") {
      const f = planningFilters.value;
      await planningStore.fetchPlannings({
        name: f.name || undefined,
        type: f.type || undefined,
        cookbook:
          f.cookbookScope === "cookbook"
            ? f.cookbookName || undefined
            : undefined,
        in_cookbook:
          f.cookbookScope === "all"
            ? undefined
            : f.cookbookScope === "cookbook",
        page_size: PAGE_SIZE,
      });
    } else {
      await cookbookStore.fetchCookbooks({
        name: cookbookFilters.value.name || undefined,
        page_size: PAGE_SIZE,
      });
    }
  } finally {
    isLoading.value = false;
  }
};

const resetFilters = () => {
  recipeFilters.value = createRecipeFilters();
  planningFilters.value = createPlanningFilters();
  cookbookFilters.value = createCookbookFilters();
  runSearch();
};

watch(searchType, runSearch);

onMounted(runSearch);

const normalize = (value: string) => value.trim().toLowerCase();

const filteredRecipes = computed(() => {
  const needle = normalize(quickFilter.value);
  const f = recipeFilters.value;
  return recipeStore.recipes.filter((recipe) => {
    if (needle && !normalize(recipe.title).includes(needle)) return false;

    if (f.prepTimeMin !== "" || f.prepTimeMax !== "") {
      const prepMinutes = sumStepMinutes(recipe.steps);
      if (f.prepTimeMin !== "" && prepMinutes < f.prepTimeMin) return false;
      if (f.prepTimeMax !== "" && prepMinutes > f.prepTimeMax) return false;
    }

    if (f.cookingTimeMin !== "" || f.cookingTimeMax !== "") {
      const cookingMinutes =
        recipe.cooking_duration !== null
          ? Number(recipe.cooking_duration)
          : null;
      if (
        f.cookingTimeMin !== "" &&
        (cookingMinutes === null || cookingMinutes < f.cookingTimeMin)
      )
        return false;
      if (
        f.cookingTimeMax !== "" &&
        (cookingMinutes === null || cookingMinutes > f.cookingTimeMax)
      )
        return false;
    }

    return true;
  });
});

const filteredPlannings = computed(() => {
  const needle = normalize(quickFilter.value);
  if (!needle) return planningStore.plannings;
  return planningStore.plannings.filter((p) =>
    normalize(p.name).includes(needle),
  );
});

const filteredCookbooks = computed(() => {
  const needle = normalize(quickFilter.value);
  if (!needle) return cookbookStore.cookbooks;
  return cookbookStore.cookbooks.filter((c) =>
    normalize(c.name).includes(needle),
  );
});

// All distinct tags carried by the recipes currently loaded (before the
// quick name filter narrows what's displayed) - lets the caller browse the
// tag vocabulary of their search results instead of guessing tag names.
const allResultTags = computed(() => {
  const byId = new Map<number, string>();
  for (const recipe of recipeStore.recipes) {
    for (const tag of recipe.tags) byId.set(tag.id, tag.name);
  }
  return [...byId.values()].sort((a, b) => a.localeCompare(b));
});

const tagsPanelOpen = ref(false);
const tagsPanelRef = ref<HTMLElement | null>(null);

onClickOutside(tagsPanelRef, () => {
  tagsPanelOpen.value = false;
});

const addTagFilter = (tagName: string) => {
  const current = recipeFilters.value.tags
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);
  if (!current.some((t) => t.toLowerCase() === tagName.toLowerCase())) {
    current.push(tagName);
    recipeFilters.value.tags = current.join(", ");
  }
  tagsPanelOpen.value = false;
  runSearch();
};

const resultCount = computed(() => {
  if (searchType.value === "recipes") return filteredRecipes.value.length;
  if (searchType.value === "plannings") return filteredPlannings.value.length;
  return filteredCookbooks.value.length;
});

const tabClasses = (key: SearchType) => [
  "flex items-center gap-[6px] border-b-2 px-1 pb-[10px] text-[13.5px] font-semibold transition",
  searchType.value === key
    ? "border-sup-dark-green text-sup-dark-green"
    : "border-transparent text-gray-400 hover:text-sup-very-gray",
];
</script>

<template>
  <div>
    <h1 class="mb-[22px] text-[24px] font-semibold text-sup-very-gray">
      Recherche
    </h1>

    <div class="mb-5 flex items-center gap-5 border-b border-sup-border">
      <button
        v-for="type in searchTypes"
        :key="type.key"
        type="button"
        :class="tabClasses(type.key)"
        @click="searchType = type.key"
      >
        <component :is="type.icon" size="xs" />
        {{ type.label }}
      </button>
    </div>

    <SearchFilters
      v-model:recipe-filters="recipeFilters"
      v-model:planning-filters="planningFilters"
      v-model:cookbook-filters="cookbookFilters"
      :type="searchType"
      @search="runSearch"
      @reset="resetFilters"
    />

    <div class="mb-4 flex flex-wrap items-center gap-3">
      <div class="relative w-full sm:w-[280px]">
        <span
          class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
        >
          <IconSearch size="xs" />
        </span>
        <input
          v-model="quickFilter"
          type="text"
          placeholder="Filtrer les résultats par nom..."
          class="w-full rounded-md border border-sup-border bg-sup-withe py-[9px] pl-9 pr-3 text-[13.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30"
        />
      </div>

      <button
        v-if="searchType === 'recipes' && cuisinePreferences.length"
        type="button"
        class="flex items-center gap-[6px] rounded-md border border-sup-border bg-sup-withe px-3 py-[9px] text-[13.5px] font-medium text-sup-very-gray hover:bg-sup-light-gray"
        title="Filtrer avec les tags enregistrés dans Paramètres"
        @click="applyCuisinePreferences"
      >
        <IconStar size="xs" />
        Mes préférences culinaires
      </button>

      <div v-if="searchType === 'recipes'" ref="tagsPanelRef" class="relative">
        <button
          type="button"
          class="flex items-center gap-[6px] rounded-md border border-sup-border bg-sup-withe px-3 py-[9px] text-[13.5px] font-medium text-sup-very-gray hover:bg-sup-light-gray"
          @click="tagsPanelOpen = !tagsPanelOpen"
        >
          <IconTag size="xs" />
          Tous les tags
        </button>

        <div
          v-if="tagsPanelOpen"
          class="absolute left-0 top-full z-10 mt-1 max-h-64 w-64 overflow-y-auto rounded-md border border-sup-border bg-sup-withe p-3 shadow-lg"
        >
          <p v-if="!allResultTags.length" class="text-[12.5px] text-gray-400">
            Aucun tag parmi les résultats actuels.
          </p>
          <div v-else class="flex flex-wrap gap-1.5">
            <button
              v-for="tag in allResultTags"
              :key="tag"
              type="button"
              class="rounded-full bg-sup-light-green/15 px-2.5 py-1 text-[11.5px] font-medium text-sup-dark-green hover:bg-sup-light-green/30"
              @click="addTagFilter(tag)"
            >
              {{ capitalizeFirst(tag) }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <p class="mb-4 text-[12px] text-gray-400">
      {{ resultCount }} résultat{{ resultCount > 1 ? "s" : "" }}
    </p>

    <RecipeSearchResults
      v-if="searchType === 'recipes'"
      :recipes="filteredRecipes"
      :is-loading="isLoading"
    />
    <PlanningSearchResults
      v-else-if="searchType === 'plannings'"
      :plannings="filteredPlannings"
      :is-loading="isLoading"
    />
    <CookbookSearchResults
      v-else
      :cookbooks="filteredCookbooks"
      :is-loading="isLoading"
    />
  </div>
</template>
