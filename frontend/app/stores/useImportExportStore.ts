// stores/useImportExportStore.ts
import { defineStore } from "pinia";
import { useApi } from "~/composables/useAPI";
import type { Recipe } from "~/stores/useRecipeStore";
import type { Cookbook } from "~/stores/cookbooks/useCookbookStore";

// The portable, DB-id-free shape produced by the export endpoints (see
// backend recipes/export.py and cookbooks/export.py) - re-imported as-is via
// the matching import endpoint, so it's treated as an opaque JSON blob here.
export type RecipeExportPayload = Record<string, unknown>;
export type CookbookExportPayload = Record<string, unknown>;

function buildQuery(params: object = {}): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export const useImportExportStore = defineStore("importExport", () => {
  const { get, post } = useApi();

  const exportingRecipes = ref(false);
  const exportingCookbooks = ref(false);
  const importingRecipes = ref(false);
  const importingCookbooks = ref(false);
  const error = ref<string | null>(null);

  // `ids` selects a subset of the caller's personal recipes to export;
  // omitted (or empty) exports all of them - see GET /api/recipes/export/.
  const exportRecipes = async (
    ids: number[] = [],
  ): Promise<RecipeExportPayload[]> => {
    exportingRecipes.value = true;
    error.value = null;
    try {
      return await get<RecipeExportPayload[]>(
        `/recipes/export/${buildQuery({ ids: ids.length ? ids.join(",") : undefined })}`,
      );
    } catch (cause) {
      error.value = "Impossible d'exporter les recettes.";
      throw cause;
    } finally {
      exportingRecipes.value = false;
    }
  };

  // Same as `exportRecipes`, for the cookbooks the caller created - see
  // GET /api/cookbooks/export/.
  const exportCookbooks = async (
    ids: number[] = [],
  ): Promise<CookbookExportPayload[]> => {
    exportingCookbooks.value = true;
    error.value = null;
    try {
      return await get<CookbookExportPayload[]>(
        `/cookbooks/export/${buildQuery({ ids: ids.length ? ids.join(",") : undefined })}`,
      );
    } catch (cause) {
      error.value = "Impossible d'exporter les cookbooks.";
      throw cause;
    } finally {
      exportingCookbooks.value = false;
    }
  };

  // `payload` is whatever was parsed from the imported .json file - either a
  // single recipe object or an array of them, per POST /api/recipes/import/.
  const importRecipes = async (payload: unknown): Promise<Recipe[]> => {
    importingRecipes.value = true;
    error.value = null;
    try {
      return await post<Recipe[]>(
        "/recipes/import/",
        payload as unknown as Record<string, unknown>,
      );
    } catch (cause) {
      error.value = "Impossible d'importer les recettes.";
      throw cause;
    } finally {
      importingRecipes.value = false;
    }
  };

  const importCookbooks = async (payload: unknown): Promise<Cookbook[]> => {
    importingCookbooks.value = true;
    error.value = null;
    try {
      return await post<Cookbook[]>(
        "/cookbooks/import/",
        payload as unknown as Record<string, unknown>,
      );
    } catch (cause) {
      error.value = "Impossible d'importer les cookbooks.";
      throw cause;
    } finally {
      importingCookbooks.value = false;
    }
  };

  return {
    exportingRecipes,
    exportingCookbooks,
    importingRecipes,
    importingCookbooks,
    error,
    exportRecipes,
    exportCookbooks,
    importRecipes,
    importCookbooks,
  };
});
