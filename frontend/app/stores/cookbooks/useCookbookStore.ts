// stores/cookbooks/useCookbookStore.ts
import { defineStore } from "pinia";
import { useApi } from "~/composables/useAPI";
import type { User } from "~/composables/useAuth";
import type { Recipe } from "~/stores/useRecipeStore";
import type { Planning } from "~/stores/usePlanningStore";

// From least to most permissive - see backend's cookbooks.permissions.ROLE_RANK.
// "admin" is never stored: it's implicit for the cookbook's own creator.
export type CookbookRole =
  | "reader"
  | "commentator"
  | "editor"
  | "creator"
  | "admin";

export interface SharedUserCookbook {
  user: User;
  role: Exclude<CookbookRole, "admin">;
  created_at: string;
  updated_at: string;
}

export interface Cookbook {
  id: number;
  name: string;
  icon: string | null;
  creator: User;
  shared_with: SharedUserCookbook[];
  recipes: Recipe[];
  plannings: Planning[];
  created_at: string;
  updated_at: string;
}

export interface CookbookWritePayload {
  name: string;
  icon?: string | null;
}

export interface CookbookListParams {
  name?: string;
  shared_with_me?: boolean;
  page?: number;
  page_size?: number;
}

export interface ShareItem {
  user?: number;
  email?: string;
  role: Exclude<CookbookRole, "admin">;
}

interface PaginatedResponse<T> {
  count: number;
  total_pages: number;
  current_page: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

function buildQuery(params: object = {}): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export const useCookbookStore = defineStore("cookbooks", () => {
  const { get, post, patch, del } = useApi();

  const cookbooks = ref<Cookbook[]>([]);
  const currentCookbook = ref<Cookbook | null>(null);
  // Name-only cache keyed by id, so a recipe/planning that belongs to a
  // cookbook can show "Dans le cookbook « X »" without re-fetching the
  // cookbook's full (recipes + plannings) payload every time.
  const cookbookNames = reactive<Record<number, string>>({});
  const pagination = reactive({
    count: 0,
    total_pages: 0,
    current_page: 1,
    next: null as string | null,
    previous: null as string | null,
  });
  const loading = ref(false);
  const error = ref<string | null>(null);

  const fetchCookbooks = async (
    params: CookbookListParams = {},
  ): Promise<Cookbook[]> => {
    loading.value = true;
    error.value = null;
    try {
      const response = await get<PaginatedResponse<Cookbook>>(
        `/cookbooks/${buildQuery(params)}`,
      );
      cookbooks.value = response.results;
      pagination.count = response.count;
      pagination.total_pages = response.total_pages;
      pagination.current_page = response.current_page;
      pagination.next = response.next;
      pagination.previous = response.previous;
      return response.results;
    } catch (cause) {
      error.value = "Impossible de charger les cookbooks.";
      throw cause;
    } finally {
      loading.value = false;
    }
  };

  const fetchCookbook = async (id: number): Promise<Cookbook> => {
    loading.value = true;
    error.value = null;
    try {
      const cookbook = await get<Cookbook>(`/cookbooks/${id}/`);
      currentCookbook.value = cookbook;
      cookbookNames[id] = cookbook.name;
      return cookbook;
    } catch (cause) {
      error.value = "Impossible de charger le cookbook.";
      throw cause;
    } finally {
      loading.value = false;
    }
  };

  const createCookbook = async (
    payload: CookbookWritePayload,
  ): Promise<Cookbook> => {
    const cookbook = await post<Cookbook>(
      "/cookbooks/",
      payload as unknown as Record<string, unknown>,
    );
    cookbooks.value = [cookbook, ...cookbooks.value];
    currentCookbook.value = cookbook;
    cookbookNames[cookbook.id] = cookbook.name;
    return cookbook;
  };

  const updateCookbook = async (
    id: number,
    payload: Partial<CookbookWritePayload>,
  ): Promise<Cookbook> => {
    const cookbook = await patch<Cookbook>(
      `/cookbooks/${id}/`,
      payload as unknown as Record<string, unknown>,
    );
    cookbooks.value = cookbooks.value.map((c: Cookbook) =>
      c.id === id ? cookbook : c,
    );
    currentCookbook.value = cookbook;
    cookbookNames[id] = cookbook.name;
    return cookbook;
  };

  const deleteCookbook = async (id: number): Promise<void> => {
    await del(`/cookbooks/${id}/`);
    cookbooks.value = cookbooks.value.filter((c: Cookbook) => c.id !== id);
    if (currentCookbook.value?.id === id) currentCookbook.value = null;
    Reflect.deleteProperty(cookbookNames, id);
  };

  const applyCookbookUpdate = (cookbook: Cookbook) => {
    cookbooks.value = cookbooks.value.map((c: Cookbook) =>
      c.id === cookbook.id ? cookbook : c,
    );
    if (currentCookbook.value?.id === cookbook.id) {
      currentCookbook.value = cookbook;
    }
  };

  const shareCookbook = async (
    id: number,
    shares: ShareItem[],
  ): Promise<Cookbook> => {
    const cookbook = await post<Cookbook>(`/cookbooks/${id}/share/`, {
      shares,
    } as unknown as Record<string, unknown>);
    applyCookbookUpdate(cookbook);
    return cookbook;
  };

  const unshareCookbook = async (
    id: number,
    userIds: number[],
  ): Promise<Cookbook> => {
    const cookbook = await post<Cookbook>(`/cookbooks/${id}/unshare/`, {
      users: userIds,
    } as unknown as Record<string, unknown>);
    applyCookbookUpdate(cookbook);
    return cookbook;
  };

  const fetchCookbookName = async (id: number): Promise<string> => {
    if (cookbookNames[id]) return cookbookNames[id];
    const cookbook = await get<Cookbook>(`/cookbooks/${id}/`);
    cookbookNames[id] = cookbook.name;
    return cookbook.name;
  };

  return {
    cookbooks,
    currentCookbook,
    cookbookNames,
    pagination,
    loading,
    error,
    fetchCookbooks,
    fetchCookbook,
    createCookbook,
    updateCookbook,
    deleteCookbook,
    shareCookbook,
    unshareCookbook,
    fetchCookbookName,
  };
});
