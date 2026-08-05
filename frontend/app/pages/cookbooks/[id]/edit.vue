<script setup lang="ts">
import CookbookEditor from "~/components/cookbook/CookbookEditor.vue";

definePageMeta({ layout: "app" });

const cookbookId = Number(useRoute().params.id);
</script>

<template>
  <CookbookEditor mode="edit" :cookbook-id="cookbookId" />
</template>
