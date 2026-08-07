<script setup lang="ts">
import { useRecipeStore } from "~/stores/useRecipeStore";
import { useCookbookStore } from "~/stores/cookbooks/useCookbookStore";
import { useImportExport } from "~/composables/useImportExport";
import type { SelectableItem } from "~/composables/useImportExport";
import ExportSelectionList from "~/components/import_export/ExportSelectionList.vue";
import ImportDropzone from "~/components/import_export/ImportDropzone.vue";
import ConfirmModal from "~/components/common/ConfirmModal.vue";
import IconRecipe from "~/components/icons/IconRecipe.vue";
import IconCookbook from "~/components/icons/IconCookbook.vue";

definePageMeta({ layout: "app" });

const recipeStore = useRecipeStore();
const cookbookStore = useCookbookStore();
const {
  store: importExportStore,
  exportRecipes,
  exportCookbooks,
  importRecipes,
  importCookbooks,
} = useImportExport();

const recipeDropzone = ref<InstanceType<typeof ImportDropzone> | null>(null);
const cookbookDropzone = ref<InstanceType<typeof ImportDropzone> | null>(null);

// Only your own personal recipes (not filed into any cookbook) are
// exportable - mirrors GET /api/recipes/export/'s own filter, so nothing
// shown here can 404 once selected.
const recipeItems = computed<SelectableItem[]>(() =>
  recipeStore.recipes.map((recipe) => ({ id: recipe.id, title: recipe.title })),
);

// Only the cookbooks you created are exportable - mirrors
// GET /api/cookbooks/export/'s own filter.
const cookbookItems = computed<SelectableItem[]>(() =>
  cookbookStore.cookbooks.map((cookbook) => ({
    id: cookbook.id,
    title: cookbook.name,
    subtitle: `${cookbook.recipes.length} recette${cookbook.recipes.length > 1 ? "s" : ""}`,
  })),
);

const loadRecipes = () =>
  recipeStore.fetchRecipes({ in_cookbook: false, page_size: 100 });
const loadCookbooks = () =>
  cookbookStore.fetchCookbooks({ shared_with_me: false, page_size: 100 });

onMounted(() => {
  loadRecipes();
  loadCookbooks();
});

// The actual export only runs once the user acknowledges the raw-JSON
// warning below - see `pendingExport` / `confirmExport`.
const pendingExport = ref<{
  kind: "recipes" | "cookbooks";
  ids: number[];
} | null>(null);
const exportConfirmOpen = computed(() => pendingExport.value !== null);

const askExportRecipes = (ids: number[]) => {
  pendingExport.value = { kind: "recipes", ids };
};
const askExportCookbooks = (ids: number[]) => {
  pendingExport.value = { kind: "cookbooks", ids };
};

const confirmExport = async () => {
  if (!pendingExport.value) return;
  const { kind, ids } = pendingExport.value;
  pendingExport.value = null;
  if (kind === "recipes") await exportRecipes(ids);
  else await exportCookbooks(ids);
};

const onImportRecipes = async (file: File) => {
  const created = await importRecipes(file);
  if (created) {
    recipeDropzone.value?.clearFile();
    await loadRecipes();
  }
};

const onImportCookbooks = async (file: File) => {
  const created = await importCookbooks(file);
  if (created) {
    cookbookDropzone.value?.clearFile();
    await loadCookbooks();
  }
};
</script>

<template>
  <div>
    <h1 class="mb-[22px] text-[24px] font-semibold text-sup-very-gray">
      Importer / Exporter
    </h1>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <section class="rounded-[10px] border border-sup-border bg-sup-withe p-5">
        <h2
          class="mb-4 flex items-center gap-2 text-[15px] font-semibold text-sup-very-gray"
        >
          <IconRecipe size="sm" />
          Recettes
        </h2>

        <h3 class="mb-2 text-[13px] font-medium text-sup-very-gray">
          Exporter
        </h3>
        <ExportSelectionList
          :items="recipeItems"
          :loading="recipeStore.loading"
          :exporting="importExportStore.exportingRecipes"
          empty-label="Aucune recette personnelle à exporter."
          @export="askExportRecipes"
        />

        <hr class="my-5 border-sup-border" />

        <h3 class="mb-2 text-[13px] font-medium text-sup-very-gray">
          Importer
        </h3>
        <ImportDropzone
          ref="recipeDropzone"
          label="Importer les recettes"
          :busy="importExportStore.importingRecipes"
          @import="onImportRecipes"
        />
      </section>

      <section class="rounded-[10px] border border-sup-border bg-sup-withe p-5">
        <h2
          class="mb-4 flex items-center gap-2 text-[15px] font-semibold text-sup-very-gray"
        >
          <IconCookbook size="sm" />
          Cookbooks
        </h2>

        <h3 class="mb-2 text-[13px] font-medium text-sup-very-gray">
          Exporter
        </h3>
        <ExportSelectionList
          :items="cookbookItems"
          :loading="cookbookStore.loading"
          :exporting="importExportStore.exportingCookbooks"
          empty-label="Aucun cookbook créé par vous à exporter."
          @export="askExportCookbooks"
        />

        <hr class="my-5 border-sup-border" />

        <h3 class="mb-2 text-[13px] font-medium text-sup-very-gray">
          Importer
        </h3>
        <ImportDropzone
          ref="cookbookDropzone"
          label="Importer les cookbooks"
          :busy="importExportStore.importingCookbooks"
          @import="onImportCookbooks"
        />
      </section>
    </div>

    <ConfirmModal
      :open="exportConfirmOpen"
      title="Exporter au format JSON"
      message="Le fichier exporté contiendra les données sélectionnées en clair, au format JSON brut (sans chiffrement ni mise en forme) : ne le partagez qu'avec des personnes de confiance."
      confirm-label="Exporter"
      checkbox-label="Je comprends que le fichier exporté sera au format brut (JSON non chiffré)."
      @close="pendingExport = null"
      @confirm="confirmExport"
    />
  </div>
</template>
