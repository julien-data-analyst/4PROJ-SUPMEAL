<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import IconChevronLeft from "~/components/icons/IconChevronLeft.vue";
import IconStar from "~/components/icons/IconStar.vue";
import IconTrash from "~/components/icons/IconTrash.vue";
import IconAlertTriangle from "~/components/icons/IconAlertTriangle.vue";
import DeleteRecipeModal from "~/components/recipes/DeleteRecipeModal.vue";
import { useRecipeStore } from "~/stores/useRecipeStore";
import {
  useRecipes,
  renderStepMarkdown,
  formatCookingDuration,
  sumStepMinutes,
} from "~/composables/useRecipes";
import { useAuth } from "~/composables/useAuth";

definePageMeta({ layout: "app" });

const route = useRoute();
const recipeId = Number(route.params.id);

const store = useRecipeStore();
const { toggleFavorite } = useRecipes();
const { user } = useAuth();

const isLoading = ref(true);
const deleteModalOpen = ref(false);

onMounted(async () => {
  isLoading.value = true;
  try {
    await store.fetchRecipe(recipeId);
  } finally {
    isLoading.value = false;
  }
});

const recipe = computed(() => store.currentRecipe);
const isOwner = computed(
  () => !!recipe.value && recipe.value.creator.id === user.value?.id,
);
const totalPrepMinutes = computed(() =>
  recipe.value ? sumStepMinutes(recipe.value.steps) : 0,
);

const onToggleFavorite = () => {
  if (recipe.value) toggleFavorite(recipe.value);
};

const confirmDelete = async () => {
  await store.deleteRecipe(recipeId);
  deleteModalOpen.value = false;
  await navigateTo("/recipes");
};
</script>

<template>
  <div class="mx-auto max-w-[900px]">
    <div class="mb-[22px] flex flex-wrap items-center justify-between gap-4">
      <NuxtLink
        to="/recipes"
        class="flex items-center gap-[6px] text-[13px] font-medium text-gray-400 hover:text-sup-dark-green"
      >
        <IconChevronLeft size="xs" />
        Retour
      </NuxtLink>

      <div v-if="recipe" class="flex flex-wrap items-center gap-[10px]">
        <AppButton
          type="button"
          variant="secondary"
          :class="recipe.is_favorite ? 'text-sup-yellow-warning!' : ''"
          @click="onToggleFavorite"
        >
          <template #icon
            ><IconStar size="xs" :filled="recipe.is_favorite"
          /></template>
          {{ recipe.is_favorite ? "Favori" : "Ajouter aux favoris" }}
        </AppButton>
        <button
          v-if="isOwner"
          type="button"
          class="inline-flex h-[34px] w-[34px] items-center justify-center rounded-md border border-red-200 text-sup-red-error transition hover:bg-sup-red-error/10"
          title="Supprimer la recette"
          @click="deleteModalOpen = true"
        >
          <IconTrash size="xs" />
        </button>
        <AppButton
          v-if="isOwner"
          variant="primary"
          :to="`/recipes/${recipeId}/edit`"
        >
          Modifier
        </AppButton>
      </div>
    </div>

    <div v-if="isLoading" class="py-16 text-center text-[13px] text-gray-400">
      Chargement de la recette...
    </div>

    <template v-else-if="recipe">
      <div class="mb-4">
        <div
          v-if="recipe.image"
          class="mb-3 h-56 w-full overflow-hidden rounded-md"
        >
          <a
            v-if="recipe.source"
            :href="recipe.source"
            target="_blank"
            rel="noopener noreferrer"
            :title="`Ouvrir la source : ${recipe.source}`"
            class="block h-full w-full"
          >
            <img
              :src="recipe.image"
              :alt="recipe.title"
              class="h-full w-full object-cover transition hover:brightness-95"
            />
          </a>
          <img
            v-else
            :src="recipe.image"
            :alt="recipe.title"
            class="h-full w-full object-cover"
          />
        </div>
        <h1 class="mb-[6px] text-[24px] font-semibold text-sup-very-gray">
          {{ recipe.title }}
        </h1>
        <div
          class="flex flex-wrap items-center gap-2 text-[12.5px] text-gray-400"
        >
          <span
            class="inline-flex items-center rounded-full border border-sup-border bg-sup-withe px-[10px] py-[3px] text-[11px] font-semibold text-gray-400"
          >
            {{ recipe.cookbook ? "Dans un cookbook" : "Personnel" }}
          </span>
          <span
            >par
            {{ recipe.creator.first_name || recipe.creator.username }}</span
          >
          <span v-if="totalPrepMinutes > 0">
            · Préparation : {{ formatCookingDuration(totalPrepMinutes) }}
          </span>
          <span v-if="recipe.cooking_duration">
            · Cuisson : {{ formatCookingDuration(recipe.cooking_duration) }}
          </span>
          <template v-if="recipe.source">
            ·
            <a
              :href="recipe.source"
              target="_blank"
              rel="noopener noreferrer"
              class="font-semibold text-sup-dark-green hover:underline"
            >
              Source
            </a>
          </template>
        </div>
        <div v-if="recipe.tags.length" class="mt-[10px] flex flex-wrap gap-1.5">
          <span
            v-for="tag in recipe.tags"
            :key="tag.id"
            class="rounded-full bg-sup-light-green/15 px-[10px] py-[3px] text-[11px] font-semibold text-sup-dark-green"
          >
            {{ tag.name }}
          </span>
        </div>
      </div>

      <div class="rounded-[10px] border border-sup-border bg-sup-withe p-6">
        <div class="grid grid-cols-1 gap-8 sm:grid-cols-[220px_1fr]">
          <div>
            <h2 class="mb-[10px] text-[17px] font-bold text-sup-dark-green">
              Ingrédients
            </h2>
            <ul class="flex flex-col gap-2 text-[13.5px] text-sup-very-gray">
              <li
                v-for="line in recipe.ingredients"
                :key="line.ingredient.id"
                class="flex items-center gap-2"
              >
                <img
                  v-if="line.ingredient.image"
                  :src="line.ingredient.image"
                  class="h-6 w-6 rounded object-cover"
                />
                <span>
                  {{ line.quantity }}{{ line.unity ? ` ${line.unity}` : "" }}
                  {{ line.ingredient.name }}
                  <span class="text-[11px] text-gray-400"
                    >({{ line.person_numbers }} pers.)</span
                  >
                </span>
              </li>
              <li
                v-if="!recipe.ingredients.length"
                class="text-[12px] text-gray-400"
              >
                Aucun ingrédient renseigné.
              </li>
            </ul>
          </div>

          <div>
            <h2 class="mb-[10px] text-[17px] font-bold text-sup-dark-green">
              Étapes
            </h2>
            <div class="flex flex-col gap-4">
              <div v-for="(step, index) in recipe.steps" :key="step.id">
                <p class="mb-1 text-[14.5px] font-bold text-sup-very-gray">
                  {{ index + 1 }}.
                  {{ step.type === "cook" ? "Cuisson" : "Préparation" }}
                </p>
                <div
                  class="text-[13.5px] text-sup-very-gray"
                  v-html="renderStepMarkdown(step.description)"
                />
              </div>
              <p v-if="!recipe.steps.length" class="text-[12px] text-gray-400">
                Aucune étape renseignée.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="!isOwner"
        class="mt-4 flex items-center gap-2 rounded-md border border-[#F0DE9A] bg-sup-yellow-warning/15 px-[14px] py-[10px] text-[12.5px] font-medium text-[#8A6D00]"
      >
        <IconAlertTriangle size="xs" class="shrink-0" />
        Vous n'avez pas la permission de modifier cette recette.
      </div>
    </template>

    <DeleteRecipeModal
      v-if="recipe"
      :open="deleteModalOpen"
      :recipe-title="recipe.title"
      @close="deleteModalOpen = false"
      @confirm="confirmDelete"
    />
  </div>
</template>
