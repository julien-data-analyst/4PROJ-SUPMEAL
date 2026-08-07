<script setup lang="ts">
import PlanningCard from "~/components/planning/PlanningCard.vue";
import type { Planning } from "~/stores/usePlanningStore";

defineProps<{ plannings: Planning[]; isLoading: boolean }>();
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
    v-else-if="plannings.length"
    class="grid grid-cols-[repeat(auto-fill,minmax(320px,1fr))] gap-4"
  >
    <PlanningCard
      v-for="planning in plannings"
      :key="planning.id"
      :planning="planning"
      :to="`/planning/${planning.id}/view`"
      :show-menu="false"
    />
  </div>

  <div
    v-else
    class="rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-10 text-center text-[13px] text-gray-400"
  >
    Aucun planning ne correspond à votre recherche.
  </div>
</template>
