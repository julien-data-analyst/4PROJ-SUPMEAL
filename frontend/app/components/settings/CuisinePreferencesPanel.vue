<script setup lang="ts">
import { useRecipeStore } from "~/stores/useRecipeStore";
import type { Tag } from "~/stores/useRecipeStore";
import { capitalizeFirst } from "~/composables/useRecipes";
import { useCuisinePreferences } from "~/composables/useCuisinePreferences";
import IconTag from "~/components/icons/IconTag.vue";
import IconClose from "~/components/icons/IconClose.vue";
import IconPlus from "~/components/icons/IconPlus.vue";

const store = useRecipeStore();
const { preferences, isPreferred, togglePreference } = useCuisinePreferences();

const search = ref("");
const suggestions = ref<Tag[]>([]);
let searchHandle: ReturnType<typeof setTimeout> | undefined;

const runSearch = () => {
  if (searchHandle) clearTimeout(searchHandle);
  searchHandle = setTimeout(async () => {
    suggestions.value = await store.fetchTags(search.value || undefined);
  }, 250);
};

watch(search, runSearch, { immediate: true });
</script>

<template>
  <div
    class="rounded-[10px] border border-sup-border bg-sup-withe p-6"
  >
    <div
      class="mb-1 flex items-center gap-2 text-[14.5px] font-bold text-sup-very-gray"
    >
      <IconTag size="xs" />
      Préférences culinaires
    </div>
    <p class="mb-3 text-[12.5px] text-gray-500">
      Choisissez vos tags préférés - le bouton « Mes préférences culinaires »
      de la page de recherche les applique en un clic.
    </p>

    <div class="mb-3 flex flex-wrap gap-1.5">
      <span
        v-for="tag in preferences"
        :key="tag"
        class="inline-flex items-center gap-1 rounded-full bg-sup-light-green/15 px-[10px] py-[3px] text-[11px] font-semibold text-sup-dark-green"
      >
        {{ capitalizeFirst(tag) }}
        <button
          type="button"
          class="hover:text-sup-red-error"
          @click="togglePreference(tag)"
        >
          <IconClose size="xs" />
        </button>
      </span>
      <span v-if="!preferences.length" class="text-[11px] text-gray-400">
        Aucune préférence enregistrée.
      </span>
    </div>

    <input
      v-model="search"
      type="text"
      placeholder="Rechercher un tag..."
      class="w-full rounded-md border border-sup-border bg-sup-withe px-3 py-[9px] text-[13.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30"
    />

    <ul
      v-if="suggestions.length"
      class="mt-2 max-h-40 overflow-y-auto rounded-md border border-sup-border"
    >
      <li v-for="s in suggestions" :key="s.id">
        <button
          type="button"
          class="flex w-full items-center justify-between px-3 py-2 text-left text-[13px] text-sup-very-gray hover:bg-sup-light-gray"
          @click="togglePreference(s.name)"
        >
          {{ capitalizeFirst(s.name) }}
          <IconClose v-if="isPreferred(s.name)" size="xs" class="text-sup-red-error" />
          <IconPlus v-else size="xs" />
        </button>
      </li>
    </ul>
  </div>
</template>
