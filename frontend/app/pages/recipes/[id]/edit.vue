<script setup lang="ts">
import RecipeEditor from "~/components/recipes/RecipeEditor.vue";

definePageMeta({ layout: "app" });

const route = useRoute();
const recipeId = computed(() => Number(route.params.id));
</script>

<template>
  <RecipeEditor mode="edit" :recipe-id="recipeId" />
</template>
