// composables/useCookbooks.ts
import { useCookbookStore } from "~/stores/cookbooks/useCookbookStore";
import type {
  Cookbook,
  CookbookRole,
} from "~/stores/cookbooks/useCookbookStore";
import { useAuth } from "~/composables/useAuth";

export const COOKBOOK_ROLE_RANK: Record<CookbookRole, number> = {
  reader: 1,
  commentator: 2,
  editor: 3,
  creator: 4,
  admin: 5,
};

export const COOKBOOK_ROLE_LABELS: Record<CookbookRole, string> = {
  reader: "Lecteur",
  commentator: "Commentateur",
  editor: "Éditeur",
  creator: "Créateur",
  admin: "Admin",
};

// The caller's role on `cookbook`, or null if they have no access at all -
// mirrors the backend's cookbooks.permissions.get_role().
export function getCookbookRole(
  cookbook: Cookbook,
  userId: number | undefined,
): CookbookRole | null {
  if (!userId) return null;
  if (cookbook.creator.id === userId) return "admin";
  const share = cookbook.shared_with.find((s) => s.user.id === userId);
  return share?.role ?? null;
}

export function hasCookbookRank(
  cookbook: Cookbook,
  userId: number | undefined,
  minimum: CookbookRole,
): boolean {
  const role = getCookbookRole(cookbook, userId);
  if (!role) return false;
  return COOKBOOK_ROLE_RANK[role] >= COOKBOOK_ROLE_RANK[minimum];
}

// The most recent activity on a cookbook: its own `updated_at` (renamed,
// icon changed) plus every recipe/planning/member's own `updated_at` -
// unlike `cookbook.updated_at` alone, which the backend never bumps just
// because something filed into it changed. ISO-8601 UTC timestamps sort
// correctly as plain strings, so no Date parsing is needed.
export function getCookbookLastActivity(cookbook: Cookbook): string {
  const timestamps = [
    cookbook.updated_at,
    ...cookbook.recipes.map((r) => r.updated_at),
    ...cookbook.plannings.map((p) => p.updated_at),
    ...cookbook.shared_with.map((s) => s.updated_at),
  ];
  return timestamps.reduce((latest, t) => (t > latest ? t : latest));
}

// Resolves the caller's own role on a cookbook from an id getter (fetching
// the cookbook if needed) - used by a recipe/planning's view page to decide
// whether to show "Modifier"/"Supprimer" for someone who didn't create it
// but has enough rank on the cookbook it's filed into.
export function useCookbookRoleFor(getId: () => number | null) {
  const store = useCookbookStore();
  const { user } = useAuth();
  const role = ref<CookbookRole | null>(null);

  watch(
    getId,
    async (id) => {
      if (!id) {
        role.value = null;
        return;
      }
      try {
        const cookbook = await store.fetchCookbook(id);
        role.value = getCookbookRole(cookbook, user.value?.id);
      } catch {
        role.value = null;
      }
    },
    { immediate: true },
  );

  return role;
}

export function useCookbooks() {
  const store = useCookbookStore();

  const fetchMyCookbooks = (search = "", page = 1) =>
    store.fetchCookbooks({
      shared_with_me: false,
      name: search || undefined,
      page,
    });

  const fetchRecentCookbooks = (limit = 3) =>
    store.fetchCookbooks({ shared_with_me: false, page_size: limit });

  const fetchSharedCookbooks = (search = "") =>
    store.fetchCookbooks({ shared_with_me: true, name: search || undefined });

  return {
    store,
    fetchMyCookbooks,
    fetchRecentCookbooks,
    fetchSharedCookbooks,
  };
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
