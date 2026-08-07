<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import CookbookCard from "~/components/cookbook/CookbookCard.vue";
import Pagination from "~/components/common/Pagination.vue";
import IconPlus from "~/components/icons/IconPlus.vue";
import IconSearch from "~/components/icons/IconSearch.vue";
import { useCookbooks } from "~/composables/useCookbooks";

definePageMeta({ layout: "app" });

const { store, fetchMyCookbooks } = useCookbooks();

const search = ref("");
const currentPage = ref(1);
const isLoading = ref(true);
let debounceHandle: ReturnType<typeof setTimeout> | undefined;

const load = async () => {
  isLoading.value = true;
  try {
    await fetchMyCookbooks(search.value, currentPage.value);
  } finally {
    isLoading.value = false;
  }
};

onMounted(load);

watch(search, () => {
  currentPage.value = 1;
  if (debounceHandle) clearTimeout(debounceHandle);
  debounceHandle = setTimeout(load, 300);
});

watch(currentPage, load);
</script>

<template>
  <div>
    <div class="mb-[22px] flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-[24px] font-semibold text-sup-very-gray">Cookbooks</h1>
      <div class="flex flex-wrap items-center gap-[10px]">
        <div class="relative w-[220px]">
          <span
            class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
          >
            <IconSearch size="xs" />
          </span>
          <input
            v-model="search"
            type="text"
            placeholder="Rechercher un cookbook..."
            class="w-full rounded-md border border-sup-border bg-sup-withe py-[9px] pl-9 pr-3 text-[13.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30"
          />
        </div>
        <AppButton variant="primary" to="/cookbooks/new">
          <template #icon><IconPlus size="xs" /></template>
          Nouveau cookbook
        </AppButton>
      </div>
    </div>

    <p class="mb-4 text-[12px] text-gray-400">
      {{ store.pagination.count }} cookbook{{
        store.pagination.count > 1 ? "s" : ""
      }}
    </p>

    <div
      v-if="isLoading"
      class="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-4"
    >
      <div
        v-for="n in 6"
        :key="n"
        class="h-[140px] animate-pulse rounded-[10px] bg-sup-border/50"
      />
    </div>

    <div
      v-else-if="store.cookbooks.length"
      class="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-4"
    >
      <CookbookCard
        v-for="cookbook in store.cookbooks"
        :key="cookbook.id"
        :cookbook="cookbook"
        :to="`/cookbooks/${cookbook.id}/view`"
      />
    </div>

    <div
      v-else
      class="rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-10 text-center text-[13px] text-gray-400"
    >
      Aucun cookbook ne correspond à votre recherche.
    </div>

    <Pagination
      v-if="!isLoading"
      v-model:current-page="currentPage"
      :total-pages="store.pagination.total_pages"
      class="mt-5"
    />
  </div>
</template>
