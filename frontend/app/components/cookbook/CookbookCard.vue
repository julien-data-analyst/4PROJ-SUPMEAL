<script setup lang="ts">
import type { Cookbook } from "~/stores/cookbooks/useCookbookStore";
import { useCookbookStore } from "~/stores/cookbooks/useCookbookStore";
import { relativeTime } from "~/composables/useRecipes";
import IconCookbook from "~/components/icons/IconCookbook.vue";
import IconDots from "~/components/icons/IconDots.vue";
import IconEye from "~/components/icons/IconEye.vue";
import IconEdit from "~/components/icons/IconEdit.vue";
import IconTrash from "~/components/icons/IconTrash.vue";
import DeleteCookbookModal from "~/components/cookbook/DeleteCookbookModal.vue";

const props = defineProps<{ cookbook: Cookbook; to: string }>();

const store = useCookbookStore();

// Mirrors RecipeCard's .ph-a..ph-g placeholder gradients, used whenever the
// cookbook has no uploaded icon.
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
  () => placeholderGradients[props.cookbook.id % placeholderGradients.length],
);

const menuOpen = ref(false);
const menuRef = ref<HTMLElement | null>(null);
const deleteModalOpen = ref(false);

onClickOutside(menuRef, () => (menuOpen.value = false));

const contentLabel = computed(() => {
  const recipeCount = props.cookbook.recipes.length;
  const planningCount = props.cookbook.plannings.length;
  return `${recipeCount} recette${recipeCount > 1 ? "s" : ""} · ${planningCount} planning${planningCount > 1 ? "s" : ""}`;
});

const openDeleteModal = () => {
  menuOpen.value = false;
  deleteModalOpen.value = true;
};

const confirmDelete = async () => {
  await store.deleteCookbook(props.cookbook.id);
  deleteModalOpen.value = false;
};

const menuItemClasses =
  "flex w-full items-center gap-2 px-3 py-2 text-left text-[13px] text-sup-very-gray hover:bg-sup-light-gray";
</script>

<template>
  <div
    class="relative flex flex-col overflow-hidden rounded-[10px] border border-sup-border bg-sup-withe transition hover:-translate-y-px hover:shadow-md"
  >
    <NuxtLink
      :to="to"
      class="absolute inset-0 z-0"
      :aria-label="cookbook.name"
    />

    <div
      class="flex h-[90px] w-full items-center justify-center overflow-hidden"
      :class="cookbook.icon ? 'bg-sup-light-gray' : placeholderClass"
    >
      <img
        v-if="cookbook.icon"
        :src="cookbook.icon"
        :alt="cookbook.name"
        class="h-full w-full object-cover"
      />
      <IconCookbook v-else size="lg" class="text-sup-very-gray/70" />
    </div>

    <div class="px-3 pb-3 pt-[10px]">
      <p class="mb-[3px] truncate text-[13px] font-semibold text-sup-very-gray">
        {{ cookbook.name }}
      </p>
      <div
        class="flex items-center justify-between gap-1.5 text-[11px] text-gray-400"
      >
        <span>{{ contentLabel }}</span>
        <span>{{ relativeTime(cookbook.updated_at) }}</span>
      </div>
    </div>

    <!-- Menu (haut-droite) -->
    <div ref="menuRef" class="absolute right-2 top-2 z-10">
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
          :to="`/cookbooks/${cookbook.id}/view`"
          :class="menuItemClasses"
          @click="menuOpen = false"
        >
          <IconEye size="xs" />
          Vue
        </NuxtLink>
        <NuxtLink
          :to="`/cookbooks/${cookbook.id}/edit`"
          :class="menuItemClasses"
          @click="menuOpen = false"
        >
          <IconEdit size="xs" />
          Modifier
        </NuxtLink>
        <button
          type="button"
          :class="[menuItemClasses, 'text-sup-red-error']"
          @click.prevent="openDeleteModal"
        >
          <IconTrash size="xs" />
          Supprimer
        </button>
      </div>
    </div>

    <DeleteCookbookModal
      :open="deleteModalOpen"
      :cookbook-name="cookbook.name"
      :recipe-count="cookbook.recipes.length"
      :planning-count="cookbook.plannings.length"
      @close="deleteModalOpen = false"
      @confirm="confirmDelete"
    />
  </div>
</template>
