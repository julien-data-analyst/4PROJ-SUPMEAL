<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import RecipeCard from "~/components/recipes/RecipeCard.vue";
import PlanningCard from "~/components/planning/PlanningCard.vue";
import IconChevronLeft from "~/components/icons/IconChevronLeft.vue";
import IconTrash from "~/components/icons/IconTrash.vue";
import IconPlus from "~/components/icons/IconPlus.vue";
import IconCookbook from "~/components/icons/IconCookbook.vue";
import DeleteCookbookModal from "~/components/cookbook/DeleteCookbookModal.vue";
import { useCookbookView } from "~/composables/useCookbooksEditView";
import { useGoBack } from "~/composables/useGoBack";

definePageMeta({ layout: "app" });

const cookbookId = Number(useRoute().params.id);
const goBack = useGoBack("/cookbooks");

const {
  isLoading,
  deleteModalOpen,
  activeTab,
  cookbook,
  isOwner,
  recipes,
  plannings,
  confirmDelete,
} = useCookbookView(cookbookId);

const tabs = [
  { key: "recettes" as const, label: "Recettes" },
  { key: "planning" as const, label: "Planning" },
];

const tabButtonClasses = (key: "recettes" | "planning") => [
  "border-b-2 px-1 pb-[10px] text-[13.5px] font-semibold transition",
  activeTab.value === key
    ? "border-sup-dark-green text-sup-dark-green"
    : "border-transparent text-gray-400 hover:text-sup-very-gray",
];
</script>

<template>
  <div>
    <div class="mb-[22px] flex flex-wrap items-center justify-between gap-4">
      <button
        type="button"
        class="flex items-center gap-[6px] text-[13px] font-medium text-gray-400 hover:text-sup-dark-green"
        @click="goBack"
      >
        <IconChevronLeft size="xs" />
        Retour
      </button>

      <div v-if="cookbook && isOwner" class="flex flex-wrap items-center gap-[10px]">
        <button
          type="button"
          class="inline-flex h-[34px] w-[34px] items-center justify-center rounded-md border border-red-200 text-sup-red-error transition hover:bg-sup-red-error/10"
          title="Supprimer le cookbook"
          @click="deleteModalOpen = true"
        >
          <IconTrash size="xs" />
        </button>
        <AppButton variant="primary" :to="`/cookbooks/${cookbookId}/edit`">
          Modifier
        </AppButton>
      </div>
    </div>

    <div v-if="isLoading" class="py-16 text-center text-[13px] text-gray-400">
      Chargement du cookbook...
    </div>

    <template v-else-if="cookbook">
      <div class="mb-6 flex items-start gap-4">
        <div
          class="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-md bg-sup-light-gray"
        >
          <img
            v-if="cookbook.icon"
            :src="cookbook.icon"
            :alt="cookbook.name"
            class="h-full w-full object-cover"
          />
          <IconCookbook v-else size="md" />
        </div>

        <div class="flex-1">
          <h1 class="mb-[6px] text-[24px] font-semibold text-sup-very-gray">
            {{ cookbook.name }}
          </h1>
          <div class="flex flex-wrap items-center gap-2 text-[12.5px] text-gray-400">
            <span>
              {{
                isOwner
                  ? "Créé par moi"
                  : `Créé par ${cookbook.creator.first_name || cookbook.creator.username}`
              }}
            </span>
            <span
              >· {{ recipes.length }} recette{{
                recipes.length > 1 ? "s" : ""
              }}</span
            >
            <span
              >· {{ plannings.length }} planning{{
                plannings.length > 1 ? "s" : ""
              }}</span
            >
          </div>
        </div>
      </div>

      <div class="mb-5 flex items-center gap-5 border-b border-sup-border">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          type="button"
          :class="tabButtonClasses(tab.key)"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <section v-if="activeTab === 'recettes'">
        <div class="mb-[14px] flex items-center justify-end">
          <AppButton variant="primary" :to="`/new?cookbook=${cookbookId}`">
            <template #icon><IconPlus size="xs" /></template>
            Ajouter une recette
          </AppButton>
        </div>

        <div
          v-if="recipes.length"
          class="grid grid-cols-[repeat(auto-fill,minmax(190px,1fr))] gap-4"
        >
          <RecipeCard
            v-for="recipe in recipes"
            :key="recipe.id"
            :recipe="recipe"
            :to="`/recipes/${recipe.id}/view`"
          />
        </div>
        <div
          v-else
          class="rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-10 text-center text-[13px] text-gray-400"
        >
          Aucune recette dans ce cookbook pour le moment.
        </div>
      </section>

      <section v-else>
        <div class="mb-[14px] flex items-center justify-end">
          <AppButton variant="primary" :to="`/planning/new?cookbook=${cookbookId}`">
            <template #icon><IconPlus size="xs" /></template>
            Nouveau planning
          </AppButton>
        </div>

        <div
          v-if="plannings.length"
          class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-4"
        >
          <PlanningCard
            v-for="planning in plannings"
            :key="planning.id"
            :planning="planning"
            :to="`/planning/${planning.id}/view`"
          />
        </div>
        <div
          v-else
          class="rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-10 text-center text-[13px] text-gray-400"
        >
          Aucun planning dans ce cookbook pour le moment.
        </div>
      </section>
    </template>

    <DeleteCookbookModal
      v-if="cookbook"
      :open="deleteModalOpen"
      :cookbook-name="cookbook.name"
      :recipe-count="recipes.length"
      :planning-count="plannings.length"
      @close="deleteModalOpen = false"
      @confirm="confirmDelete"
    />
  </div>
</template>
