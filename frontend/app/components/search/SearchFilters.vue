<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import IconSearch from "~/components/icons/IconSearch.vue";
import CatalogMultiSelect from "~/components/search/CatalogMultiSelect.vue";
import { PLANNING_TYPE_LABELS } from "~/composables/usePlanning";
import { useRecipeStore } from "~/stores/useRecipeStore";
import type {
  SearchType,
  RecipeFilterState,
  PlanningFilterState,
  CookbookFilterState,
} from "~/composables/useSearch";

withDefaults(defineProps<{ type: SearchType; showCookbookScope?: boolean }>(), {
  showCookbookScope: true,
});

const emit = defineEmits<{ search: []; reset: [] }>();

const recipeFilters = defineModel<RecipeFilterState>("recipeFilters", {
  required: true,
});
const planningFilters = defineModel<PlanningFilterState>("planningFilters", {
  required: true,
});
const cookbookFilters = defineModel<CookbookFilterState>("cookbookFilters", {
  required: true,
});

const recipeStore = useRecipeStore();
const fetchTagOptions = (search: string) =>
  recipeStore.fetchTags(search || undefined);
const fetchIngredientOptions = (search: string) =>
  recipeStore.fetchIngredients(search || undefined);

const fieldInputClasses =
  "w-full rounded-md border border-sup-border bg-sup-withe px-3 py-[9px] text-[13.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30";
const fieldLabelClasses =
  "mb-1.5 block text-[12.5px] font-semibold text-sup-very-gray";
const rangeInputClasses =
  "w-full min-w-0 rounded-md border border-sup-border bg-sup-withe px-3 py-[9px] text-[13.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30";
</script>

<template>
  <div class="mb-4 rounded-[10px] border border-sup-border bg-sup-withe p-5">
    <div
      v-if="type === 'recipes'"
      class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
    >
      <div>
        <label :class="fieldLabelClasses" for="filter-recipe-name">Nom</label>
        <input
          id="filter-recipe-name"
          v-model="recipeFilters.name"
          type="text"
          placeholder="Nom de la recette..."
          :class="fieldInputClasses"
        />
      </div>
      <div>
        <CatalogMultiSelect
          v-model="recipeFilters.ingredients"
          label="Ingrédients"
          search-placeholder="Rechercher un ingrédient..."
          empty-label="Aucun ingrédient."
          :fetch-options="fetchIngredientOptions"
        />
      </div>
      <div>
        <CatalogMultiSelect
          v-model="recipeFilters.tags"
          label="Tags"
          search-placeholder="Rechercher un tag..."
          empty-label="Aucun tag."
          capitalize-labels
          :fetch-options="fetchTagOptions"
        />
      </div>
      <div v-if="showCookbookScope">
        <label :class="fieldLabelClasses" for="filter-recipe-cookbook-scope">
          Cookbook
        </label>
        <select
          id="filter-recipe-cookbook-scope"
          v-model="recipeFilters.cookbookScope"
          :class="fieldInputClasses"
        >
          <option value="all">Toutes</option>
          <option value="personal">Personnelles</option>
          <option value="cookbook">Dans un cookbook</option>
        </select>
        <input
          v-if="recipeFilters.cookbookScope === 'cookbook'"
          v-model="recipeFilters.cookbookName"
          type="text"
          placeholder="Nom du cookbook..."
          class="mt-2"
          :class="fieldInputClasses"
        />
      </div>
      <div>
        <label :class="fieldLabelClasses" for="filter-recipe-planning-scope">
          Planning
        </label>
        <select
          id="filter-recipe-planning-scope"
          v-model="recipeFilters.planningScope"
          :class="fieldInputClasses"
        >
          <option value="all">Toutes</option>
          <option value="not_planned">Non programmées</option>
          <option value="planned">Dans un planning</option>
        </select>
        <input
          v-if="recipeFilters.planningScope === 'planned'"
          v-model="recipeFilters.planningName"
          type="text"
          placeholder="Nom du planning..."
          class="mt-2"
          :class="fieldInputClasses"
        />
      </div>
      <div>
        <label :class="fieldLabelClasses" for="filter-recipe-favorite">
          Favoris
        </label>
        <select
          id="filter-recipe-favorite"
          v-model="recipeFilters.favoriteScope"
          :class="fieldInputClasses"
        >
          <option value="all">Toutes</option>
          <option value="favorite">Favorites uniquement</option>
          <option value="not_favorite">Non favorites</option>
        </select>
      </div>
      <div>
        <label :class="fieldLabelClasses">Préparation (min)</label>
        <div class="flex items-center gap-2">
          <input
            v-model.number="recipeFilters.prepTimeMin"
            type="number"
            min="0"
            placeholder="Min"
            :class="rangeInputClasses"
          />
          <span class="text-gray-400">-</span>
          <input
            v-model.number="recipeFilters.prepTimeMax"
            type="number"
            min="0"
            placeholder="Max"
            :class="rangeInputClasses"
          />
        </div>
      </div>
      <div>
        <label :class="fieldLabelClasses">Cuisson (min)</label>
        <div class="flex items-center gap-2">
          <input
            v-model.number="recipeFilters.cookingTimeMin"
            type="number"
            min="0"
            placeholder="Min"
            :class="rangeInputClasses"
          />
          <span class="text-gray-400">-</span>
          <input
            v-model.number="recipeFilters.cookingTimeMax"
            type="number"
            min="0"
            placeholder="Max"
            :class="rangeInputClasses"
          />
        </div>
      </div>
    </div>

    <div
      v-else-if="type === 'plannings'"
      class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
    >
      <div>
        <label :class="fieldLabelClasses" for="filter-planning-name">
          Nom
        </label>
        <input
          id="filter-planning-name"
          v-model="planningFilters.name"
          type="text"
          placeholder="Nom du planning..."
          :class="fieldInputClasses"
        />
      </div>
      <div>
        <label :class="fieldLabelClasses" for="filter-planning-type">
          Type
        </label>
        <select
          id="filter-planning-type"
          v-model="planningFilters.type"
          :class="fieldInputClasses"
        >
          <option value="">Tous</option>
          <option value="journalier">
            {{ PLANNING_TYPE_LABELS.journalier }}
          </option>
          <option value="hebdomadaire">
            {{ PLANNING_TYPE_LABELS.hebdomadaire }}
          </option>
        </select>
      </div>
      <div v-if="showCookbookScope">
        <label :class="fieldLabelClasses" for="filter-planning-cookbook-scope">
          Cookbook
        </label>
        <select
          id="filter-planning-cookbook-scope"
          v-model="planningFilters.cookbookScope"
          :class="fieldInputClasses"
        >
          <option value="all">Tous</option>
          <option value="personal">Personnels</option>
          <option value="cookbook">Dans un cookbook</option>
        </select>
        <input
          v-if="planningFilters.cookbookScope === 'cookbook'"
          v-model="planningFilters.cookbookName"
          type="text"
          placeholder="Nom du cookbook..."
          class="mt-2"
          :class="fieldInputClasses"
        />
      </div>
    </div>

    <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div>
        <label :class="fieldLabelClasses" for="filter-cookbook-name">
          Nom
        </label>
        <input
          id="filter-cookbook-name"
          v-model="cookbookFilters.name"
          type="text"
          placeholder="Nom du cookbook..."
          :class="fieldInputClasses"
        />
      </div>
    </div>

    <div class="mt-4 flex items-center justify-end gap-3">
      <AppButton variant="ghost" @click="emit('reset')">
        Réinitialiser
      </AppButton>
      <AppButton variant="primary" @click="emit('search')">
        <template #icon><IconSearch size="xs" /></template>
        Rechercher
      </AppButton>
    </div>
  </div>
</template>
