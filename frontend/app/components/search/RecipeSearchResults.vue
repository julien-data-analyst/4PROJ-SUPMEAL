<script setup lang="ts">
import RecipeCard from "~/components/recipes/RecipeCard.vue";
import type { Recipe } from "~/stores/useRecipeStore";

defineProps<{ recipes: Recipe[]; isLoading: boolean }>();
</script>

<template>
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
    v-else-if="recipes.length"
    class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-4"
  >
    <RecipeCard
      v-for="recipe in recipes"
      :key="recipe.id"
      :recipe="recipe"
      :to="`/recipes/${recipe.id}/view`"
      :show-menu="false"
    />
  </div>

  <div
    v-else
    class="rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-10 text-center text-[13px] text-gray-400"
  >
    Aucune recette ne correspond à votre recherche.
  </div>
</template>
