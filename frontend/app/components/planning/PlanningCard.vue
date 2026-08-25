<script setup lang="ts">
import type { Planning } from "~/stores/usePlanningStore";
import { usePlanningStore } from "~/stores/usePlanningStore";
import { useToastStore } from "~/stores/useToastStore";
import { relativeTime } from "~/composables/useRecipes";
import { PLANNING_TYPE_LABELS } from "~/composables/usePlanning";
import IconCalendar from "~/components/icons/IconCalendar.vue";
import IconDots from "~/components/icons/IconDots.vue";
import IconEye from "~/components/icons/IconEye.vue";
import IconEdit from "~/components/icons/IconEdit.vue";
import IconTrash from "~/components/icons/IconTrash.vue";
import DeletePlanningModal from "~/components/planning/DeletePlanningModal.vue";

const props = withDefaults(
  defineProps<{
    planning: Planning;
    to: string;
    // See RecipeCard's identical props - gates the menu for a shared
    // cookbook's reader/commentator (canEdit=false) or editor (canManage=
    // false) role.
    canEdit?: boolean;
    canManage?: boolean;
    // Hides the "..." options menu entirely - used by the search page,
    // where results can come from cookbooks the caller has no role on
    // at all.
    showMenu?: boolean;
  }>(),
  { canEdit: true, canManage: true, showMenu: true },
);

const store = usePlanningStore();
const toast = useToastStore();

const menuOpen = ref(false);
const menuRef = ref<HTMLElement | null>(null);
const deleteModalOpen = ref(false);

onClickOutside(menuRef, () => {
  menuOpen.value = false;
});

const mealCountLabel = computed(() => {
  const count = props.planning.meals.length;
  return `${count} repas planifié${count > 1 ? "s" : ""}`;
});

const openDeleteModal = () => {
  menuOpen.value = false;
  deleteModalOpen.value = true;
};

const confirmDelete = async () => {
  await store.deletePlanning(props.planning.id);
  deleteModalOpen.value = false;
  toast.success("Planning supprimé.");
};

const menuItemClasses =
  "flex w-full items-center gap-2 px-3 py-2 text-left text-[13px] text-sup-very-gray hover:bg-sup-light-gray";
</script>

<template>
  <div
    class="relative flex items-center gap-3 rounded-[10px] border border-sup-border bg-sup-withe p-5 pr-10 transition hover:-translate-y-px hover:shadow-md"
  >
    <NuxtLink
      :to="to"
      class="absolute inset-0 z-0"
      :aria-label="planning.name"
    />

    <div
      class="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-md bg-sup-light-gray"
    >
      <img
        v-if="planning.icon"
        :src="planning.icon"
        :alt="planning.name"
        class="h-8 w-8 object-contain"
      />
      <IconCalendar v-else size="sm" />
    </div>

    <div class="min-w-0 flex-1">
      <p class="truncate text-[14.5px] font-semibold text-sup-very-gray">
        {{ planning.name }}
      </p>
      <p class="truncate text-[11.5px] text-gray-400">
        {{ PLANNING_TYPE_LABELS[planning.type] }} · {{ mealCountLabel }} ·
        {{ relativeTime(planning.updated_at) }}
      </p>
    </div>

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
          :to="`/planning/${planning.id}/view`"
          :class="menuItemClasses"
          @click="menuOpen = false"
        >
          <IconEye size="xs" />
          Vue
        </NuxtLink>
        <NuxtLink
          v-if="canEdit"
          :to="`/planning/${planning.id}/edit`"
          :class="menuItemClasses"
          @click="menuOpen = false"
        >
          <IconEdit size="xs" />
          Modifier
        </NuxtLink>
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
    </div>

    <DeletePlanningModal
      :open="deleteModalOpen"
      :planning-name="planning.name"
      @close="deleteModalOpen = false"
      @confirm="confirmDelete"
    />
  </div>
</template>
