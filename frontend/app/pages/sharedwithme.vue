<script setup lang="ts">
import SharedCookbookCard from "~/components/cookbook/SharedCookbookCard.vue";
import IconSearch from "~/components/icons/IconSearch.vue";
import IconShared from "~/components/icons/IconShared.vue";
import { useCookbooks, getCookbookRole } from "~/composables/useCookbooks";
import { useAuth } from "~/composables/useAuth";
import type { CookbookRole } from "~/stores/cookbooks/useCookbookStore";

definePageMeta({ layout: "app" });

const { store, fetchSharedCookbooks } = useCookbooks();
const { user } = useAuth();

const search = ref("");
const isLoading = ref(true);
let debounceHandle: ReturnType<typeof setTimeout> | undefined;

const load = async () => {
  isLoading.value = true;
  try {
    await fetchSharedCookbooks(search.value);
  } finally {
    isLoading.value = false;
  }
};

onMounted(load);

watch(search, () => {
  if (debounceHandle) clearTimeout(debounceHandle);
  debounceHandle = setTimeout(load, 300);
});

// A cookbook only shows up here via `shared_with_me=true`, so the caller
// always has a real (non-admin) role on it - never null.
const sharedCookbooks = computed(() =>
  store.cookbooks.map((cookbook) => ({
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
      <h1 class="text-[24px] font-semibold text-sup-very-gray">
        Partagés avec moi
      </h1>
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
    </div>

    <p class="mb-4 text-[12px] text-gray-400">
      {{ store.pagination.count }} cookbook{{
        store.pagination.count > 1 ? "s" : ""
      }}
      partagé{{ store.pagination.count > 1 ? "s" : "" }} avec moi
    </p>

    <div v-if="isLoading" class="flex flex-col gap-3">
      <div
        v-for="n in 4"
        :key="n"
        class="h-[68px] animate-pulse rounded-[10px] bg-sup-border/50"
      />
    </div>

    <div v-else-if="sharedCookbooks.length" class="flex flex-col gap-3">
      <SharedCookbookCard
        v-for="{ cookbook, role } in sharedCookbooks"
        :key="cookbook.id"
        :cookbook="cookbook"
        :role="role"
        :to="`/cookbooks/${cookbook.id}/view`"
      />
    </div>

    <div
      v-else
      class="flex items-center gap-3 rounded-[10px] border border-dashed border-sup-border bg-sup-withe p-8 text-[13px] text-gray-400"
    >
      <IconShared size="sm" />
      Aucun cookbook n'a encore été partagé avec vous.
    </div>
  </div>
</template>
