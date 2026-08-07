// composables/useImportExport.ts
import { useImportExportStore } from "~/stores/useImportExportStore";
import { useToastStore } from "~/stores/useToastStore";
import type { Recipe } from "~/stores/useRecipeStore";
import type { Cookbook } from "~/stores/cookbooks/useCookbookStore";

// A row in the export selection list (ExportSelectionList.vue) - `id` maps
// straight to the `ids` filter accepted by GET /api/recipes/export/ and
// GET /api/cookbooks/export/.
export interface SelectableItem {
  id: number;
  title: string;
  subtitle?: string;
}

// Strict extension check (not MIME type, which browsers/OSes report
// inconsistently for .json - e.g. "" or "text/plain" depending on origin).
export function isJsonFile(file: File): boolean {
  return file.name.toLowerCase().endsWith(".json");
}

export function readJsonFile(file: File): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        resolve(JSON.parse(reader.result as string));
      } catch {
        reject(new Error("Le fichier ne contient pas un JSON valide."));
      }
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}

export function downloadJson(data: unknown, filename: string): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function pluralize(count: number, singular: string, plural: string): string {
  return count > 1 ? plural : singular;
}

export function useImportExport() {
  const store = useImportExportStore();
  const toast = useToastStore();

  // `ids` empty exports every one of the caller's personal recipes/cookbooks.
  const exportRecipes = async (ids: number[] = []): Promise<void> => {
    try {
      const data = await store.exportRecipes(ids);
      downloadJson(data, "recipes_export.json");
      toast.success(
        `${data.length} ${pluralize(data.length, "recette exportée", "recettes exportées")}.`,
      );
    } catch {
      toast.error(store.error || "Impossible d'exporter les recettes.");
    }
  };

  const exportCookbooks = async (ids: number[] = []): Promise<void> => {
    try {
      const data = await store.exportCookbooks(ids);
      downloadJson(data, "cookbooks_export.json");
      toast.success(
        `${data.length} ${pluralize(data.length, "cookbook exporté", "cookbooks exportés")}.`,
      );
    } catch {
      toast.error(store.error || "Impossible d'exporter les cookbooks.");
    }
  };

  const importRecipes = async (file: File): Promise<Recipe[] | null> => {
    if (!isJsonFile(file)) {
      toast.error("Seuls les fichiers .json sont acceptés.");
      return null;
    }
    let payload: unknown;
    try {
      payload = await readJsonFile(file);
    } catch (cause) {
      toast.error(
        cause instanceof Error
          ? cause.message
          : "Le fichier ne contient pas un JSON valide.",
      );
      return null;
    }
    try {
      const created = await store.importRecipes(payload);
      toast.success(
        `${created.length} ${pluralize(created.length, "recette importée", "recettes importées")}.`,
      );
      return created;
    } catch {
      toast.error(store.error || "Impossible d'importer les recettes.");
      return null;
    }
  };

  const importCookbooks = async (file: File): Promise<Cookbook[] | null> => {
    if (!isJsonFile(file)) {
      toast.error("Seuls les fichiers .json sont acceptés.");
      return null;
    }
    let payload: unknown;
    try {
      payload = await readJsonFile(file);
    } catch (cause) {
      toast.error(
        cause instanceof Error
          ? cause.message
          : "Le fichier ne contient pas un JSON valide.",
      );
      return null;
    }
    try {
      const created = await store.importCookbooks(payload);
      toast.success(
        `${created.length} ${pluralize(created.length, "cookbook importé", "cookbooks importés")}.`,
      );
      return created;
    } catch {
      toast.error(store.error || "Impossible d'importer les cookbooks.");
      return null;
    }
  };

  return {
    store,
    exportRecipes,
    exportCookbooks,
    importRecipes,
    importCookbooks,
  };
}
