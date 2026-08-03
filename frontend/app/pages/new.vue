<script setup lang="ts">
import RecipeEditor from "~/components/recipes/RecipeEditor.vue";

definePageMeta({ layout: "app" });
</script>

<template>
  <RecipeEditor mode="create" />
</template>
