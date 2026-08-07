<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import RecipeCard from "~/components/recipes/RecipeCard.vue";
import PlanningCard from "~/components/planning/PlanningCard.vue";
import CookbookMembersPanel from "~/components/cookbook/CookbookMembersPanel.vue";
import SearchFilters from "~/components/search/SearchFilters.vue";
import Pagination from "~/components/common/Pagination.vue";
import IconChevronLeft from "~/components/icons/IconChevronLeft.vue";
import IconTrash from "~/components/icons/IconTrash.vue";
import IconPlus from "~/components/icons/IconPlus.vue";
import IconCookbook from "~/components/icons/IconCookbook.vue";
import DeleteCookbookModal from "~/components/cookbook/DeleteCookbookModal.vue";
import { useCookbookView } from "~/composables/useCookbooksEditView";
import { useGoBack } from "~/composables/useGoBack";
import { COOKBOOK_ROLE_LABELS } from "~/composables/useCookbooks";
import {
  createRecipeFilters,
  createPlanningFilters,
  createCookbookFilters,
  filterRecipesLocally,
  filterPlanningsLocally,
} from "~/composables/useSearch";

definePageMeta({ layout: "app" });

const cookbookId = Number(useRoute().params.id);
const goBack = useGoBack("/cookbooks");

const {
  isLoading,
  deleteModalOpen,
  activeTab,
  cookbook,
  isOwner,
  myRole,
  canManageContent,
  canEditContent,
  recipes,
  plannings,
  confirmDelete,
} = useCookbookView(cookbookId);

const tabs = [
  { key: "recettes" as const, label: "Recettes" },
  { key: "planning" as const, label: "Planning" },
  { key: "membres" as const, label: "Membres" },
];

// Reuses the exact same filter block as the general search page (see
// `~/pages/search.vue`), scoped to this one cookbook's already-loaded
// `recipes`/`plannings` (no backend call - everything's filtered
// client-side, see `filterRecipesLocally`/`filterPlanningsLocally`).
// `cookbookFilters` is unused (the "Cookbook" scope field is hidden via
// `show-cookbook-scope="false"`, meaningless once already inside one) but
// still required to satisfy <SearchFilters>'s model contract.
//
// `recipeFilters`/`planningFilters` are the draft values bound to the
// inputs; `appliedRecipeFilters`/`appliedPlanningFilters` are what the list
// is actually filtered by - only synced from the draft on "Rechercher"
// (@search), matching the general search page's click-to-apply behaviour
// instead of filtering on every keystroke.
const recipeFilters = ref(createRecipeFilters());
const planningFilters = ref(createPlanningFilters());
const cookbookFilters = ref(createCookbookFilters());
const appliedRecipeFilters = ref(createRecipeFilters());
const appliedPlanningFilters = ref(createPlanningFilters());

const RECIPES_PAGE_SIZE = 8;
const PLANNINGS_PAGE_SIZE = 6;
const recipePage = ref(1);
const planningPage = ref(1);

const filteredRecipes = computed(() =>
  filterRecipesLocally(recipes.value, appliedRecipeFilters.value),
);
const recipeTotalPages = computed(() =>
  Math.max(1, Math.ceil(filteredRecipes.value.length / RECIPES_PAGE_SIZE)),
);
const pagedRecipes = computed(() => {
  const start = (recipePage.value - 1) * RECIPES_PAGE_SIZE;
  return filteredRecipes.value.slice(start, start + RECIPES_PAGE_SIZE);
});

const filteredPlannings = computed(() =>
  filterPlanningsLocally(plannings.value, appliedPlanningFilters.value),
);
const planningTotalPages = computed(() =>
  Math.max(1, Math.ceil(filteredPlannings.value.length / PLANNINGS_PAGE_SIZE)),
);
const pagedPlannings = computed(() => {
  const start = (planningPage.value - 1) * PLANNINGS_PAGE_SIZE;
  return filteredPlannings.value.slice(start, start + PLANNINGS_PAGE_SIZE);
});

const applyRecipeFilters = () => {
  appliedRecipeFilters.value = { ...recipeFilters.value };
  recipePage.value = 1;
};
const applyPlanningFilters = () => {
  appliedPlanningFilters.value = { ...planningFilters.value };
  planningPage.value = 1;
};

const resetRecipeFilters = () => {
  recipeFilters.value = createRecipeFilters();
  appliedRecipeFilters.value = createRecipeFilters();
  recipePage.value = 1;
};
const resetPlanningFilters = () => {
  planningFilters.value = createPlanningFilters();
  appliedPlanningFilters.value = createPlanningFilters();
  planningPage.value = 1;
};

const tabButtonClasses = (key: "recettes" | "planning" | "membres") => [
  "border-b-2 px-1 pb-[10px] text-[13.5px] font-semibold transition",
  activeTab.value === key
    ? "border-sup-dark-green text-sup-dark-green"
    : "border-transparent text-gray-400 hover:text-sup-very-gray",
];
</script>

<template>
  <div>
    <div class="mb-[22px] flex flex-wrap items-center justify-between gap-4">
      <button
        type="button"
        class="flex items-center gap-[6px] text-[13px] font-medium text-gray-400 hover:text-sup-dark-green"
        @click="goBack"
      >
        <IconChevronLeft size="xs" />
        Retour
      </button>

      <div
        v-if="cookbook && isOwner"
        class="flex flex-wrap items-center gap-[10px]"
      >
        <button
          type="button"
          class="inline-flex h-[34px] w-[34px] items-center justify-center rounded-md border border-red-200 text-sup-red-error transition hover:bg-sup-red-error/10"
          title="Supprimer le cookbook"
          @click="deleteModalOpen = true"
        >
          <IconTrash size="xs" />
        </button>
        <AppButton variant="primary" :to="`/cookbooks/${cookbookId}/edit`">
          Modifier
        </AppButton>
      </div>
    </div>

    <div v-if="isLoading" class="py-16 text-center text-[13px] text-gray-400">
      Chargement du cookbook...
    </div>

    <template v-else-if="cookbook">
      <div class="mb-6 flex items-start gap-4">
        <div
          class="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-md bg-sup-light-gray"
        >
          <img
            v-if="cookbook.icon"
            :src="cookbook.icon"
            :alt="cookbook.name"
            class="h-full w-full object-cover"
          />
          <IconCookbook v-else size="md" />
        </div>

        <div class="flex-1">
          <h1 class="mb-[6px] text-[24px] font-semibold text-sup-very-gray">
            {{ cookbook.name }}
          </h1>
          <div
            class="flex flex-wrap items-center gap-2 text-[12.5px] text-gray-400"
          >
            <span>
              {{
                isOwner
                  ? "Créé par moi"
                  : `Créé par ${cookbook.creator.first_name || cookbook.creator.username}`
              }}
            </span>
            <span
              v-if="!isOwner && myRole"
              class="inline-flex items-center rounded-full bg-sup-light-green/15 px-[10px] py-[3px] text-[11px] font-semibold text-sup-dark-green"
            >
              {{ COOKBOOK_ROLE_LABELS[myRole] }}
            </span>
            <span
              >· {{ recipes.length }} recette{{
                recipes.length > 1 ? "s" : ""
              }}</span
            >
            <span
              >· {{ plannings.length }} planning{{
                plannings.length > 1 ? "s" : ""
              }}</span
            >
          </div>
        </div>
      </div>

      <div class="mb-5 flex items-center gap-5 border-b border-sup-border">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          type="button"
          :class="tabButtonClasses(tab.key)"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <section v-if="activeTab === 'recettes'">
        <div
          v-if="canManageContent"
          class="mb-[14px] flex items-center justify-end"
        >
          <AppButton variant="primary" :to="`/new?cookbook=${cookbookId}`">
            <template #icon><IconPlus size="xs" /></template>
            Ajouter une recette
          </AppButton>
        </div>

        <SearchFilters
          v-if="recipes.length"
          v-model:recipe-filters="recipeFilters"
          v-model:planning-filters="planningFilters"
          v-model:cookbook-filters="cookbookFilters"
          type="recipes"
          :show-cookbook-scope="false"
          @search="applyRecipeFilters"
          @reset="resetRecipeFilters"
        />

        <div
          v-if="pagedRecipes.length"
          class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-4"
        >
          <RecipeCard
            v-for="recipe in pagedRecipes"
            :key="recipe.id"
            :recipe="recipe"
            :to="`/recipes/${recipe.id}/view`"
            :can-edit="canEditContent"
            :can-manage="canManageContent"
            :can-reassign-cookbook="false"
          />
        </div>
        <div
          v-else
          class="rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-10 text-center text-[13px] text-gray-400"
        >
          {{
            recipes.length
              ? "Aucune recette ne correspond à ces filtres."
              : "Aucune recette dans ce cookbook pour le moment."
          }}
        </div>

        <Pagination
          v-model:current-page="recipePage"
          :total-pages="recipeTotalPages"
          class="mt-5"
        />
      </section>

      <section v-else-if="activeTab === 'planning'">
        <div
          v-if="canManageContent"
          class="mb-[14px] flex items-center justify-end"
        >
          <AppButton
            variant="primary"
            :to="`/planning/new?cookbook=${cookbookId}`"
          >
            <template #icon><IconPlus size="xs" /></template>
            Nouveau planning
          </AppButton>
        </div>

        <SearchFilters
          v-if="plannings.length"
          v-model:recipe-filters="recipeFilters"
          v-model:planning-filters="planningFilters"
          v-model:cookbook-filters="cookbookFilters"
          type="plannings"
          :show-cookbook-scope="false"
          @search="applyPlanningFilters"
          @reset="resetPlanningFilters"
        />

        <div
          v-if="pagedPlannings.length"
          class="grid grid-cols-[repeat(auto-fill,minmax(320px,1fr))] gap-4"
        >
          <PlanningCard
            v-for="planning in pagedPlannings"
            :key="planning.id"
            :planning="planning"
            :to="`/planning/${planning.id}/view`"
            :can-edit="canEditContent"
            :can-manage="canManageContent"
            :can-reassign-cookbook="false"
          />
        </div>
        <div
          v-else
          class="rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-10 text-center text-[13px] text-gray-400"
        >
          {{
            plannings.length
              ? "Aucun planning ne correspond à ces filtres."
              : "Aucun planning dans ce cookbook pour le moment."
          }}
        </div>

        <Pagination
          v-model:current-page="planningPage"
          :total-pages="planningTotalPages"
          class="mt-5"
        />
      </section>

      <section v-else>
        <CookbookMembersPanel
          :cookbook-id="cookbookId"
          :creator="cookbook.creator"
          :shared-with="cookbook.shared_with"
          :is-owner="isOwner"
        />
      </section>
    </template>

    <DeleteCookbookModal
      v-if="cookbook"
      :open="deleteModalOpen"
      :cookbook-name="cookbook.name"
      :recipes="recipes"
      :plannings="plannings"
      @close="deleteModalOpen = false"
      @confirm="confirmDelete"
    />
  </div>
</template>
