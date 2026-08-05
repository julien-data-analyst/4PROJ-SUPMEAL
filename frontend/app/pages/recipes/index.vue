<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import RecipeCard from "~/components/recipes/RecipeCard.vue";
import IconPlus from "~/components/icons/IconPlus.vue";
import IconSearch from "~/components/icons/IconSearch.vue";
import { useRecipes, sortFavoritesFirst } from "~/composables/useRecipes";

definePageMeta({ layout: "app" });

const { store, fetchMyRecipes } = useRecipes();

const search = ref("");
const isLoading = ref(true);
let debounceHandle: ReturnType<typeof setTimeout> | undefined;

const load = async () => {
  isLoading.value = true;
  try {
    await fetchMyRecipes(search.value);
  } finally {
    isLoading.value = false;
  }
};

onMounted(load);

watch(search, () => {
  if (debounceHandle) clearTimeout(debounceHandle);
  debounceHandle = setTimeout(load, 300);
});

const sortedRecipes = computed(() => sortFavoritesFirst(store.recipes));
</script>

<template>
  <div>
    <div class="mb-[22px] flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-[24px] font-semibold text-sup-very-gray">Mes recettes</h1>
      <div class="flex flex-wrap items-center gap-[10px]">
        <div class="relative w-[220px]">
          <span
            class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
          >
            <IconSearch size="xs" />
          </span>
          <input
            v-model="search"
            type="text"
            placeholder="Rechercher une recette..."
            class="w-full rounded-md border border-sup-border bg-sup-withe py-[9px] pl-9 pr-3 text-[13.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30"
          />
        </div>
        <AppButton variant="primary" to="/new">
          <template #icon><IconPlus size="xs" /></template>
          Nouvelle recette
        </AppButton>
      </div>
    </div>

    <p class="mb-4 text-[12px] text-gray-400">
      {{ store.pagination.count }} recette{{
        store.pagination.count > 1 ? "s" : ""
      }}
      personnelle{{ store.pagination.count > 1 ? "s" : "" }}
    </p>

    <div
      v-if="isLoading"
      class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-4"
    >
      <div
        v-for="n in 8"
        :key="n"
        class="h-[205px] animate-pulse rounded-[10px] bg-sup-border/50"
      />
    </div>

    <div
      v-else-if="sortedRecipes.length"
      class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-4"
    >
      <RecipeCard
        v-for="recipe in sortedRecipes"
        :key="recipe.id"
        :recipe="recipe"
        :to="`/recipes/${recipe.id}/view`"
      />
    </div>

    <div
      v-else
      class="rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-10 text-center text-[13px] text-gray-400"
    >
      Aucune recette ne correspond à votre recherche.
    </div>
  </div>
</template>
