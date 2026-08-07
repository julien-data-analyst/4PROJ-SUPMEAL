<script setup lang="ts">
import CookbookCard from "~/components/cookbook/CookbookCard.vue";
import type { Cookbook } from "~/stores/cookbooks/useCookbookStore";

defineProps<{ cookbooks: Cookbook[]; isLoading: boolean }>();
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
    v-else-if="cookbooks.length"
    class="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-4"
  >
    <CookbookCard
      v-for="cookbook in cookbooks"
      :key="cookbook.id"
      :cookbook="cookbook"
      :to="`/cookbooks/${cookbook.id}/view`"
      :show-menu="false"
    />
  </div>

  <div
    v-else
    class="rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-10 text-center text-[13px] text-gray-400"
  >
    Aucun cookbook ne correspond à votre recherche.
  </div>
</template>
