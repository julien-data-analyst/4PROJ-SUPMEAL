<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import IconDownload from "~/components/icons/IconDownload.vue";
import IconSearch from "~/components/icons/IconSearch.vue";
import IconChevron from "~/components/icons/IconChevron.vue";
import type { SelectableItem } from "~/composables/useImportExport";

const PAGE_SIZE = 5;

const props = withDefaults(
  defineProps<{
    items: SelectableItem[];
    loading?: boolean;
    exporting?: boolean;
    emptyLabel?: string;
    searchPlaceholder?: string;
  }>(),
  {
    loading: false,
    exporting: false,
    emptyLabel: "Rien à exporter.",
    searchPlaceholder: "Rechercher par nom...",
  },
);

const emit = defineEmits<{ export: [ids: number[]] }>();

const selected = ref<Set<number>>(new Set());
const search = ref("");
const currentPage = ref(1);

// Drop any selected id that disappeared from the list (e.g. after a refetch)
// so the "N / total sélectionnés" count and the export payload stay accurate.
watch(
  () => props.items,
  (items) => {
    const ids = new Set(items.map((item) => item.id));
    selected.value = new Set([...selected.value].filter((id) => ids.has(id)));
  },
);

const filteredItems = computed(() => {
  const term = search.value.trim().toLowerCase();
  if (!term) return props.items;
  return props.items.filter((item) => item.title.toLowerCase().includes(term));
});

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredItems.value.length / PAGE_SIZE)),
);

// A new search or a shorter filtered list can leave `currentPage` past the
// end - snap it back into range instead of showing a blank page.
watch([search, totalPages], () => {
  if (currentPage.value > totalPages.value)
    currentPage.value = totalPages.value;
  if (currentPage.value < 1) currentPage.value = 1;
});

const pagedItems = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE;
  return filteredItems.value.slice(start, start + PAGE_SIZE);
});

// Windowed page numbers (at most 5 buttons) centered on the current page.
const pageNumbers = computed(() => {
  const total = totalPages.value;
  const windowSize = Math.min(5, total);
  let start = Math.max(1, currentPage.value - Math.floor(windowSize / 2));
  const end = Math.min(total, start + windowSize - 1);
  start = Math.max(1, end - windowSize + 1);
  return Array.from({ length: end - start + 1 }, (_, i) => start + i);
});

const goToPage = (page: number) => {
  currentPage.value = Math.min(Math.max(1, page), totalPages.value);
};

// "Tout sélectionner" applies to what's currently filtered (so a search can
// be used to select a whole batch at once), not just the visible page.
const allFilteredSelected = computed(
  () =>
    filteredItems.value.length > 0 &&
    filteredItems.value.every((item) => selected.value.has(item.id)),
);

const toggleAll = () => {
  const next = new Set(selected.value);
  if (allFilteredSelected.value) {
    for (const item of filteredItems.value) next.delete(item.id);
  } else {
    for (const item of filteredItems.value) next.add(item.id);
  }
  selected.value = next;
};

const toggleOne = (id: number) => {
  const next = new Set(selected.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  selected.value = next;
};

const doExport = () => {
  if (!selected.value.size) return;
  emit("export", [...selected.value]);
};
</script>

<template>
  <div>
    <div class="relative mb-3">
      <span
        class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
      >
        <IconSearch size="xs" />
      </span>
      <input
        v-model="search"
        type="text"
        :placeholder="searchPlaceholder"
        class="w-full rounded-md border border-sup-border bg-sup-withe py-[9px] pl-9 pr-3 text-[13.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30"
      />
    </div>

    <div class="mb-2 flex items-center justify-between">
      <label class="flex items-center gap-2 text-[12.5px] text-sup-very-gray">
        <input
          type="checkbox"
          class="h-4 w-4 rounded border-sup-border accent-sup-dark-green"
          :checked="allFilteredSelected"
          :disabled="!filteredItems.length"
          @change="toggleAll"
        />
        Tout sélectionner
      </label>
      <span class="text-[12px] text-gray-400">
        {{ selected.size }} / {{ items.length }} sélectionné{{
          selected.size > 1 ? "s" : ""
        }}
      </span>
    </div>

    <div
      v-if="loading"
      class="rounded-[10px] border border-sup-border bg-sup-withe p-6 text-center text-[13px] text-gray-400"
    >
      Chargement...
    </div>

    <div
      v-else-if="!items.length"
      class="rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-6 text-center text-[13px] text-gray-400"
    >
      {{ emptyLabel }}
    </div>

    <div
      v-else-if="!filteredItems.length"
      class="rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-6 text-center text-[13px] text-gray-400"
    >
      Aucun résultat pour « {{ search }} ».
    </div>

    <template v-else>
      <ul
        class="divide-y divide-sup-border rounded-[10px] border border-sup-border bg-sup-withe"
      >
        <li v-for="item in pagedItems" :key="item.id">
          <label
            class="flex cursor-pointer items-center gap-3 px-4 py-2.5 hover:bg-sup-light-gray"
          >
            <input
              type="checkbox"
              class="h-4 w-4 shrink-0 rounded border-sup-border accent-sup-dark-green"
              :checked="selected.has(item.id)"
              @change="toggleOne(item.id)"
            />
            <span class="min-w-0 flex-1">
              <span
                class="block truncate text-[13px] font-medium text-sup-very-gray"
              >
                {{ item.title }}
              </span>
              <span
                v-if="item.subtitle"
                class="block truncate text-[11.5px] text-gray-400"
              >
                {{ item.subtitle }}
              </span>
            </span>
          </label>
        </li>
      </ul>

      <div v-if="totalPages > 1" class="mt-2 flex items-center justify-between">
        <span class="text-[11.5px] text-gray-400">
          Page {{ currentPage }} / {{ totalPages }}
        </span>
        <div class="flex items-center gap-1">
          <button
            type="button"
            class="flex h-7 w-7 items-center justify-center rounded-md text-gray-400 hover:bg-sup-light-gray hover:text-sup-very-gray disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent"
            :disabled="currentPage === 1"
            title="Page précédente"
            @click="goToPage(currentPage - 1)"
          >
            <IconChevron size="xs" direction="left" />
          </button>
          <button
            v-for="page in pageNumbers"
            :key="page"
            type="button"
            class="flex h-7 w-7 items-center justify-center rounded-md text-[12px] font-medium"
            :class="
              page === currentPage
                ? 'bg-sup-dark-green text-sup-withe'
                : 'text-sup-very-gray hover:bg-sup-light-gray'
            "
            @click="goToPage(page)"
          >
            {{ page }}
          </button>
          <button
            type="button"
            class="flex h-7 w-7 items-center justify-center rounded-md text-gray-400 hover:bg-sup-light-gray hover:text-sup-very-gray disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent"
            :disabled="currentPage === totalPages"
            title="Page suivante"
            @click="goToPage(currentPage + 1)"
          >
            <IconChevron size="xs" direction="right" />
          </button>
        </div>
      </div>
    </template>

    <AppButton
      class="mt-3"
      variant="secondary"
      :disabled="!selected.size || exporting"
      @click="doExport"
    >
      <template #icon><IconDownload size="xs" /></template>
      {{ exporting ? "Export en cours..." : `Exporter (${selected.size})` }}
    </AppButton>
  </div>
</template>
