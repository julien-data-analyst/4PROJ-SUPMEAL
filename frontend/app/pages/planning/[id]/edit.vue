<script setup lang="ts">
import PlanningEditor from "~/components/planning/PlanningEditor.vue";

definePageMeta({ layout: "app" });

const route = useRoute();
const planningId = computed(() => Number(route.params.id));
</script>

<template>
  <PlanningEditor mode="edit" :planning-id="planningId" />
</template>
