<script setup lang="ts">
import type { Recipe } from "~/stores/useRecipeStore";
import { relativeTime, useRecipes } from "~/composables/useRecipes";
import { useRecipeStore } from "~/stores/useRecipeStore";
import { useToastStore } from "~/stores/useToastStore";
import { useCookbookName } from "~/composables/useCookbooks";
import IconBookmark from "~/components/icons/IconBookmark.vue";
import IconDots from "~/components/icons/IconDots.vue";
import IconEye from "~/components/icons/IconEye.vue";
import IconEdit from "~/components/icons/IconEdit.vue";
import IconTrash from "~/components/icons/IconTrash.vue";
import IconCookbook from "~/components/icons/IconCookbook.vue";
import IconChevron from "~/components/icons/IconChevron.vue";
import DeleteRecipeModal from "~/components/recipes/DeleteRecipeModal.vue";
import AssignCookbookMenu from "~/components/cookbook/AssignCookbookMenu.vue";

const props = withDefaults(
  defineProps<{
    recipe: Recipe;
    to: string;
    // Gate the "Modifier"/"Cookbook"/"Supprimer" menu items for a shared
    // cookbook's reader/commentator (canEdit=false) or editor (canManage=
    // false) role - see cookbooks.permissions.CookbookItemPermission on the
    // backend. Both default to true: the card's own creator (personal
    // lists, or a cookbook's admin/creator) always has full rights.
    canEdit?: boolean;
    canManage?: boolean;
    // Separately hides just the "Cookbook" (reassign) menu item, even when
    // canManage allows deleting - a cookbook's own Recettes tab renders
    // this card for a recipe already filed there, where moving it to a
    // *different* cookbook has no place in the UI.
    canReassignCookbook?: boolean;
    // Hides the "..." options menu (Vue/Modifier/Cookbook/Supprimer)
    // entirely - used by the search page, where results can come from
    // cookbooks the caller has no role on at all.
    showMenu?: boolean;
  }>(),
  { canEdit: true, canManage: true, canReassignCookbook: true, showMenu: true },
);

const store = useRecipeStore();
const toast = useToastStore();
const { toggleFavorite } = useRecipes();

// Mirrors the prototype's .ph-a..ph-g placeholder gradients (no stock photos
// in the design system - recipes without an uploaded image get one of these).
const placeholderGradients = [
  "bg-gradient-to-br from-[#FCEBB6] to-[#F1C40F]",
  "bg-gradient-to-br from-[#C7F0A4] to-[#84FA16]",
  "bg-gradient-to-br from-[#FBC7BB] to-[#E74C3C]",
  "bg-gradient-to-br from-[#AEE9C7] to-[#1A7F02]",
  "bg-gradient-to-br from-[#F7D9E3] to-[#E68FAE]",
  "bg-gradient-to-br from-[#BEE3F5] to-[#5EA8D6]",
  "bg-gradient-to-br from-[#EAFBDA] to-[#2AC204]",
];

const placeholderClass = computed(
  () => placeholderGradients[props.recipe.id % placeholderGradients.length],
);

const cookbookName = useCookbookName(() => props.recipe.cookbook);

const isFavoriteBusy = ref(false);
const menuOpen = ref(false);
const cookbookMenuOpen = ref(false);
const menuRef = ref<HTMLElement | null>(null);
const deleteModalOpen = ref(false);
const tagsExpanded = ref(false);

onClickOutside(menuRef, () => {
  menuOpen.value = false;
  cookbookMenuOpen.value = false;
});

const onToggleFavorite = async () => {
  if (isFavoriteBusy.value) return;
  isFavoriteBusy.value = true;
  try {
    await toggleFavorite(props.recipe);
  } finally {
    isFavoriteBusy.value = false;
  }
};

const openDeleteModal = () => {
  menuOpen.value = false;
  deleteModalOpen.value = true;
};

const confirmDelete = async () => {
  await store.deleteRecipe(props.recipe.id);
  deleteModalOpen.value = false;
};

const openCookbookMenu = () => {
  menuOpen.value = false;
  cookbookMenuOpen.value = true;
};

const onSelectCookbook = async (cookbook: { id: number; name: string }) => {
  await store.updateRecipe(props.recipe.id, { cookbook: cookbook.id });
  // The card's list (personal recipes, a cookbook's own recipes...) no
  // longer includes this recipe once it's filed elsewhere.
  store.recipes = store.recipes.filter((r) => r.id !== props.recipe.id);
  cookbookMenuOpen.value = false;
  toast.success(`Recette ajoutée au cookbook « ${cookbook.name} ».`);
};

const menuItemClasses =
  "flex w-full items-center gap-2 px-3 py-2 text-left text-[13px] text-sup-very-gray hover:bg-sup-light-gray";
</script>

<template>
  <div
    class="relative flex flex-col rounded-[10px] border border-sup-border bg-sup-withe transition hover:-translate-y-px hover:shadow-md"
  >
    <NuxtLink
      :to="to"
      class="absolute inset-0 z-0"
      :aria-label="recipe.title"
    />

    <div
      class="flex h-[150px] w-full items-center justify-center overflow-hidden rounded-t-[10px]"
      :class="recipe.image ? 'bg-sup-light-gray' : placeholderClass"
    >
      <img
        v-if="recipe.image"
        :src="recipe.image"
        :alt="recipe.title"
        class="h-full w-full object-cover"
      />
      <span v-else class="text-[34px]">🍽️</span>
    </div>

    <div class="px-4 pb-4 pt-3">
      <p class="mb-1 truncate text-[14.5px] font-semibold text-sup-very-gray">
        {{ recipe.title }}
      </p>
      <div
        class="flex items-center justify-between gap-1.5 text-[11.5px] text-gray-400"
      >
        <span class="flex items-center gap-1">
          {{ relativeTime(recipe.updated_at) }}
          <button
            v-if="recipe.tags.length"
            type="button"
            class="relative z-10 flex items-center text-gray-400 hover:text-sup-dark-green"
            :title="tagsExpanded ? 'Masquer les tags' : 'Voir les tags'"
            @click.stop.prevent="tagsExpanded = !tagsExpanded"
          >
            <IconChevron size="xs" :direction="tagsExpanded ? 'up' : 'down'" />
          </button>
        </span>
        <NuxtLink
          v-if="recipe.cookbook"
          :to="`/cookbooks/${recipe.cookbook}/view`"
          class="relative z-10 max-w-[110px] truncate font-semibold text-sup-dark-green hover:underline"
          @click.stop
        >
          {{ cookbookName || "Cookbook" }}
        </NuxtLink>
        <span v-else>Recette</span>
      </div>

      <div
        v-if="tagsExpanded && recipe.tags.length"
        class="mt-1.5 flex flex-wrap gap-1"
      >
        <span
          v-for="tag in recipe.tags"
          :key="tag.id"
          class="rounded-full bg-sup-light-green/15 px-2 py-0.5 text-[10px] font-medium text-sup-dark-green"
        >
          {{ tag.name }}
        </span>
      </div>
    </div>

    <!-- Favori (haut-gauche) -->
    <button
      type="button"
      class="absolute left-2 top-2 z-10 flex h-7 w-7 items-center justify-center rounded-full bg-sup-withe/90 shadow-sm transition hover:bg-sup-withe disabled:opacity-60"
      :class="recipe.is_favorite ? 'text-sup-dark-green' : 'text-gray-400'"
      :disabled="isFavoriteBusy"
      :title="
        recipe.is_favorite ? 'Retirer des favoris' : 'Ajouter aux favoris'
      "
      @click.stop.prevent="onToggleFavorite"
    >
      <IconBookmark size="xs" :filled="recipe.is_favorite" />
    </button>

    <!-- Menu (haut-droite) -->
    <div v-if="showMenu" ref="menuRef" class="absolute right-2 top-2 z-10">
      <button
        type="button"
        class="flex h-7 w-7 items-center justify-center rounded-full bg-sup-withe/90 text-sup-very-gray shadow-sm transition hover:bg-sup-withe"
        title="Options"
        @click.stop.prevent="menuOpen = !menuOpen"
      >
        <IconDots size="xs" />
      </button>

      <div
        v-if="menuOpen"
        class="absolute right-0 top-full mt-1 w-36 overflow-hidden rounded-md border border-sup-border bg-sup-withe py-1 shadow-lg"
        @click.stop
      >
        <NuxtLink
          :to="`/recipes/${recipe.id}/view`"
          :class="menuItemClasses"
          @click="menuOpen = false"
        >
          <IconEye size="xs" />
          Vue
        </NuxtLink>
        <NuxtLink
          v-if="canEdit"
          :to="`/recipes/${recipe.id}/edit`"
          :class="menuItemClasses"
          @click="menuOpen = false"
        >
          <IconEdit size="xs" />
          Modifier
        </NuxtLink>
        <button
          v-if="canManage && canReassignCookbook"
          type="button"
          :class="menuItemClasses"
          @click.prevent="openCookbookMenu"
        >
          <IconCookbook size="xs" />
          Cookbook
        </button>
        <button
          v-if="canManage"
          type="button"
          :class="[menuItemClasses, 'text-sup-red-error']"
          @click.prevent="openDeleteModal"
        >
          <IconTrash size="xs" />
          Supprimer
        </button>
      </div>

      <div
        v-if="cookbookMenuOpen"
        class="absolute right-0 top-full mt-1 overflow-hidden rounded-md border border-sup-border bg-sup-withe shadow-lg"
      >
        <AssignCookbookMenu
          :current-cookbook-id="recipe.cookbook"
          @select="onSelectCookbook"
        />
      </div>
    </div>

    <DeleteRecipeModal
      :open="deleteModalOpen"
      :recipe-title="recipe.title"
      :used-in-plannings="recipe.used_in_plannings"
      @close="deleteModalOpen = false"
      @confirm="confirmDelete"
    />
  </div>
</template>
