<script setup lang="ts">
import { useCookbookStore } from "~/stores/cookbooks/useCookbookStore";
import { useAuth } from "~/composables/useAuth";
import { hasCookbookRank } from "~/composables/useCookbooks";
import IconCookbook from "~/components/icons/IconCookbook.vue";
import IconSearch from "~/components/icons/IconSearch.vue";

const props = defineProps<{ currentCookbookId?: number | null }>();
const emit = defineEmits<{
  select: [cookbook: { id: number; name: string }];
}>();

const store = useCookbookStore();
const { user } = useAuth();
const query = ref("");
const results = ref<{ id: number; name: string }[]>([]);
const isLoading = ref(false);
let searchHandle: ReturnType<typeof setTimeout> | undefined;

const search = async () => {
  isLoading.value = true;
  try {
    const found = await store.fetchCookbooks({
      name: query.value || undefined,
      page_size: 8,
    });
    // Filing a recipe/planning into a cookbook requires "creator" rank
    // there (see the backend's validate_cookbook) - a shared cookbook
    // where the caller is only reader/commentator/editor isn't offered.
    results.value = found.filter(
      (c) =>
        c.id !== props.currentCookbookId &&
        hasCookbookRank(c, user.value?.id, "creator"),
    );
  } finally {
    isLoading.value = false;
  }
};

onMounted(search);

const onInput = () => {
  if (searchHandle) clearTimeout(searchHandle);
  searchHandle = setTimeout(search, 250);
};
</script>

<template>
  <div class="w-60 p-2" @click.stop>
    <div class="relative mb-2">
      <span
        class="pointer-events-none absolute left-2 top-1/2 -translate-y-1/2 text-gray-400"
      >
        <IconSearch size="xs" />
      </span>
      <input
        v-model="query"
        type="text"
        placeholder="Rechercher un cookbook..."
        class="w-full rounded-md border border-sup-border bg-sup-withe py-1.5 pl-7 pr-2 text-[12.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30"
        @input="onInput"
      />
    </div>

    <ul class="max-h-48 overflow-y-auto">
      <li v-for="cookbook in results" :key="cookbook.id">
        <button
          type="button"
          class="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-[12.5px] text-sup-very-gray hover:bg-sup-light-gray"
          @click="emit('select', cookbook)"
        >
          <IconCookbook size="xs" class="shrink-0 text-gray-400" />
          <span class="truncate">{{ cookbook.name }}</span>
        </button>
      </li>
      <li
        v-if="!isLoading && !results.length"
        class="px-2 py-1.5 text-[12px] text-gray-400"
      >
        Aucun cookbook trouvé.
      </li>
    </ul>
  </div>
</template>
