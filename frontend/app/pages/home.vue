<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import RecipeCard from "~/components/recipes/RecipeCard.vue";
import IconPlus from "~/components/icons/IconPlus.vue";
import IconUpload from "~/components/icons/IconUpload.vue";
import IconDownload from "~/components/icons/IconDownload.vue";
import IconCookbook from "~/components/icons/IconCookbook.vue";
import IconCalendar from "~/components/icons/IconCalendar.vue";
import { useRecipes, sortFavoritesFirst } from "~/composables/useRecipes";

definePageMeta({ layout: "app" });

const { store, fetchRecentRecipes } = useRecipes();

const isLoading = ref(true);

onMounted(async () => {
  try {
    await fetchRecentRecipes(3);
  } finally {
    isLoading.value = false;
  }
});

// store.recipes only holds this page's fetched batch (page_size: 3), so
// favoriting/deleting a card here reactively re-sorts/shrinks this list too.
const recentRecipes = computed(() => {
  const byDate = [...store.recipes].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );
  return sortFavoritesFirst(byDate);
});
</script>

<template>
  <div>
    <div class="mb-[22px] flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-[24px] font-semibold text-sup-very-gray">Accueil</h1>
      <div class="flex flex-wrap items-center gap-[10px]">
        <AppButton variant="secondary" to="/import_export">
          <template #icon><IconUpload size="xs" /></template>
          Importer
        </AppButton>
        <AppButton variant="secondary" to="/import_export">
          <template #icon><IconDownload size="xs" /></template>
          Exporter
        </AppButton>
        <AppButton variant="primary" to="/new">
          <template #icon><IconPlus size="xs" /></template>
          Nouveau
        </AppButton>
      </div>
    </div>

    <!-- Récemment ajoutées -->
    <section class="mb-[30px]">
      <div class="mb-[14px] flex items-center justify-between">
        <h2 class="text-[18px] font-semibold text-sup-very-gray">
          Récemment ajoutées
        </h2>
        <NuxtLink
          to="/recipes"
          class="text-[13px] font-semibold text-sup-dark-green hover:underline"
        >
          Voir tout
        </NuxtLink>
      </div>

      <div
        v-if="isLoading"
        class="grid grid-cols-[repeat(auto-fill,minmax(190px,1fr))] gap-4"
      >
        <div
          v-for="n in 3"
          :key="n"
          class="h-[150px] animate-pulse rounded-[10px] bg-sup-border/50"
        />
      </div>

      <div
        v-else-if="recentRecipes.length"
        class="grid grid-cols-[repeat(auto-fill,minmax(190px,1fr))] gap-4"
      >
        <RecipeCard
          v-for="recipe in recentRecipes"
          :key="recipe.id"
          :recipe="recipe"
          :to="`/recipes/${recipe.id}/view`"
        />
      </div>

      <div
        v-else
        class="rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-8 text-center text-[13px] text-gray-400"
      >
        Vous n'avez pas encore de recette. Créez votre première recette
        personnelle !
      </div>
    </section>

    <!-- Mes cookbooks -->
    <section class="mb-[30px]">
      <div class="mb-[14px] flex items-center justify-between">
        <h2 class="text-[18px] font-semibold text-sup-very-gray">
          Mes cookbooks
        </h2>
      </div>
      <div
        class="flex items-center gap-3 rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-6 text-[13px] text-gray-400"
      >
        <IconCookbook size="sm" />
        Bientôt disponible.
      </div>
    </section>

    <!-- Mes plannings repas -->
    <section>
      <div class="mb-[14px] flex items-center justify-between">
        <h2 class="text-[18px] font-semibold text-sup-very-gray">
          Mes plannings repas
        </h2>
      </div>
      <div
        class="flex items-center gap-3 rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-6 text-[13px] text-gray-400"
      >
        <IconCalendar size="sm" />
        Bientôt disponible.
      </div>
    </section>
  </div>
</template>
