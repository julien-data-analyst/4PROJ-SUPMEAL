<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import RecipeCard from "~/components/recipes/RecipeCard.vue";
import PlanningCard from "~/components/planning/PlanningCard.vue";
import CookbookCard from "~/components/cookbook/CookbookCard.vue";
import SharedCookbookCard from "~/components/cookbook/SharedCookbookCard.vue";
import IconPlus from "~/components/icons/IconPlus.vue";
import IconUpload from "~/components/icons/IconUpload.vue";
import IconDownload from "~/components/icons/IconDownload.vue";
import IconCookbook from "~/components/icons/IconCookbook.vue";
import IconShared from "~/components/icons/IconShared.vue";
import IconRecipe from "~/components/icons/IconRecipe.vue";
import IconCalendar from "~/components/icons/IconCalendar.vue";
import { useRecipes, sortFavoritesFirst } from "~/composables/useRecipes";
import { usePlanning } from "~/composables/usePlanning";
import {
  useCookbooks,
  getCookbookRole,
  getCookbookLastActivity,
} from "~/composables/useCookbooks";
import { useAuth } from "~/composables/useAuth";
import type {
  Cookbook,
  CookbookRole,
} from "~/stores/cookbooks/useCookbookStore";

definePageMeta({ layout: "app" });

const { store, fetchRecentRecipes } = useRecipes();
const { store: planningStore, fetchRecentPlannings } = usePlanning();
const { fetchRecentCookbooks, fetchSharedCookbooks } = useCookbooks();
const { user } = useAuth();

const isLoading = ref(true);
const isPlanningLoading = ref(true);
const isCookbookLoading = ref(true);
const isSharedActivityLoading = ref(true);

// Both cookbook sections below hit the same underlying store, whose
// `cookbooks`/`pagination` only ever hold the *last* fetch's results - kept
// as page-local lists instead so "Mes cookbooks" and "Cookbooks partagés"
// don't clobber each other.
const myCookbooks = ref<Cookbook[]>([]);
const sharedActivityCookbooks = ref<Cookbook[]>([]);

onMounted(async () => {
  try {
    await fetchRecentRecipes(3);
  } finally {
    isLoading.value = false;
  }
});

onMounted(async () => {
  try {
    await fetchRecentPlannings(3);
  } finally {
    isPlanningLoading.value = false;
  }
});

onMounted(async () => {
  try {
    myCookbooks.value = await fetchRecentCookbooks(3);
  } finally {
    isCookbookLoading.value = false;
  }
});

onMounted(async () => {
  try {
    // No `page_size` filter for the activity ranking: the backend sorts by
    // `-updated_at` on the cookbook itself, which doesn't reflect nested
    // recipe/planning/member changes - so a wider page is pulled and
    // re-sorted client-side by real last activity before keeping the top 3.
    const shared = await fetchSharedCookbooks();
    sharedActivityCookbooks.value = [...shared]
      .sort((a, b) =>
        getCookbookLastActivity(b).localeCompare(getCookbookLastActivity(a)),
      )
      .slice(0, 3);
  } finally {
    isSharedActivityLoading.value = false;
  }
});

// store.recipes only holds this page's fetched batch (page_size: 3), so
// favoriting/deleting a card here reactively re-sorts/shrinks this list too.
// Sorted by `updated_at` (recently modified), matching the "Mes cookbooks"/
// "Mes plannings repas" sections below rather than creation date.
const recentRecipes = computed(() => {
  const byDate = [...store.recipes].sort(
    (a, b) =>
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
  );
  return sortFavoritesFirst(byDate);
});

const recentPlannings = computed(() =>
  [...planningStore.plannings].sort(
    (a, b) =>
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
  ),
);

const newMenuOpen = ref(false);
const newMenuRef = ref<HTMLElement | null>(null);
onClickOutside(newMenuRef, () => (newMenuOpen.value = false));

const newMenuItemClasses =
  "flex w-full items-center gap-2 px-3 py-2 text-left text-[13px] text-sup-very-gray hover:bg-sup-light-gray";

const sharedActivityRoles = computed(() =>
  sharedActivityCookbooks.value.map((cookbook) => ({
    cookbook,
    role: (getCookbookRole(cookbook, user.value?.id) ?? "reader") as Exclude<
      CookbookRole,
      "admin"
    >,
  })),
);
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
        <div ref="newMenuRef" class="relative">
          <AppButton
            type="button"
            variant="primary"
            @click="newMenuOpen = !newMenuOpen"
          >
            <template #icon><IconPlus size="xs" /></template>
            Nouveau
          </AppButton>

          <div
            v-if="newMenuOpen"
            class="absolute right-0 top-full z-20 mt-1 w-48 overflow-hidden rounded-md border border-sup-border bg-sup-withe py-1 shadow-lg"
          >
            <NuxtLink
              to="/new"
              :class="newMenuItemClasses"
              @click="newMenuOpen = false"
            >
              <IconRecipe size="xs" />
              Nouvelle recette
            </NuxtLink>
            <NuxtLink
              to="/planning/new"
              :class="newMenuItemClasses"
              @click="newMenuOpen = false"
            >
              <IconCalendar size="xs" />
              Nouveau planning
            </NuxtLink>
            <NuxtLink
              to="/cookbooks/new"
              :class="newMenuItemClasses"
              @click="newMenuOpen = false"
            >
              <IconCookbook size="xs" />
              Nouveau cookbook
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>

    <!-- Mes recettes -->
    <section class="mb-[30px]">
      <div class="mb-[14px] flex items-center justify-between">
        <h2 class="text-[18px] font-semibold text-sup-very-gray">
          Mes recettes
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
        class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-4"
      >
        <div
          v-for="n in 3"
          :key="n"
          class="h-[205px] animate-pulse rounded-[10px] bg-sup-border/50"
        />
      </div>

      <div
        v-else-if="recentRecipes.length"
        class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-4"
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
        class="flex items-center gap-3 rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-6 text-[13px] text-gray-400"
      >
        <IconRecipe size="sm" />  
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
        <NuxtLink
          to="/cookbooks"
          class="text-[13px] font-semibold text-sup-dark-green hover:underline"
        >
          Voir tout
        </NuxtLink>
      </div>

      <div
        v-if="isCookbookLoading"
        class="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-4"
      >
        <div
          v-for="n in 3"
          :key="n"
          class="h-[140px] animate-pulse rounded-[10px] bg-sup-border/50"
        />
      </div>

      <div
        v-else-if="myCookbooks.length"
        class="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-4"
      >
        <CookbookCard
          v-for="cookbook in myCookbooks"
          :key="cookbook.id"
          :cookbook="cookbook"
          :to="`/cookbooks/${cookbook.id}/view`"
        />
      </div>

      <div
        v-else
        class="flex items-center gap-3 rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-6 text-[13px] text-gray-400"
      >
        <IconCookbook size="sm" />
        Vous n'avez pas encore de cookbook. Créez-en un pour regrouper vos
        recettes et plannings !
      </div>
    </section>

    <!-- Mes plannings repas -->
    <section>
      <div class="mb-[14px] flex items-center justify-between">
        <h2 class="text-[18px] font-semibold text-sup-very-gray">
          Mes plannings repas
        </h2>
        <NuxtLink
          to="/planning"
          class="text-[13px] font-semibold text-sup-dark-green hover:underline"
        >
          Voir tout
        </NuxtLink>
      </div>

      <div
        v-if="isPlanningLoading"
        class="grid grid-cols-[repeat(auto-fill,minmax(320px,1fr))] gap-4"
      >
        <div
          v-for="n in 3"
          :key="n"
          class="h-[84px] animate-pulse rounded-[10px] bg-sup-border/50"
        />
      </div>

      <div
        v-else-if="recentPlannings.length"
        class="grid grid-cols-[repeat(auto-fill,minmax(320px,1fr))] gap-4"
      >
        <PlanningCard
          v-for="planning in recentPlannings"
          :key="planning.id"
          :planning="planning"
          :to="`/planning/${planning.id}/view`"
        />
      </div>

      <div
        v-else
        class="flex items-center gap-3 rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-6 text-[13px] text-gray-400"
      >
        <IconCalendar size="sm"/>
        Vous n'avez pas encore de planning. Créez votre premier planning de
        repas !
      </div>
    </section>

    <!-- Cookbooks partagés récemment modifiés -->
    <section class="mt-[30px]">
      <div class="mb-[14px] flex items-center justify-between">
        <h2 class="text-[18px] font-semibold text-sup-very-gray">
          Cookbooks partagés récemment modifiés
        </h2>
        <NuxtLink
          to="/sharedwithme"
          class="text-[13px] font-semibold text-sup-dark-green hover:underline"
        >
          Voir tout
        </NuxtLink>
      </div>

      <div v-if="isSharedActivityLoading" class="flex flex-col gap-3">
        <div
          v-for="n in 3"
          :key="n"
          class="h-[68px] animate-pulse rounded-[10px] bg-sup-border/50"
        />
      </div>

      <div v-else-if="sharedActivityRoles.length" class="flex flex-col gap-3">
        <SharedCookbookCard
          v-for="{ cookbook, role } in sharedActivityRoles"
          :key="cookbook.id"
          :cookbook="cookbook"
          :role="role"
          :activity-at="getCookbookLastActivity(cookbook)"
          :to="`/cookbooks/${cookbook.id}/view`"
        />
      </div>

      <div
        v-else
        class="flex items-center gap-3 rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-6 text-[13px] text-gray-400"
      >
        <IconShared size="sm" />
        Aucun cookbook n'a encore été partagé avec vous.
      </div>
    </section>
  </div>
</template>
