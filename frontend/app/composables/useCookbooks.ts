// composables/useCookbooks.ts
import { useCookbookStore } from "~/stores/cookbooks/useCookbookStore";

export function useCookbooks() {
  const store = useCookbookStore();

  const fetchMyCookbooks = (search = "") =>
    store.fetchCookbooks({ name: search || undefined });

  const fetchRecentCookbooks = async (limit = 3): Promise<void> => {
    await store.fetchCookbooks({ page_size: limit });
  };

  return { store, fetchMyCookbooks, fetchRecentCookbooks };
}

// Resolves and caches a cookbook's name from an id getter - used to show
// "Dans le cookbook « X »" under a recipe/planning's title in its edit and
// view pages. Takes a getter (rather than a Ref) so callers can pass a
// plain computed expression without importing Vue's Ref type.
export function useCookbookName(getId: () => number | null) {
  const store = useCookbookStore();
  const name = ref<string | null>(null);

  watch(
    getId,
    async (id) => {
      if (!id) {
        name.value = null;
        return;
      }
      try {
        name.value = await store.fetchCookbookName(id);
      } catch {
        name.value = null;
      }
    },
    { immediate: true },
  );

  return name;
}
