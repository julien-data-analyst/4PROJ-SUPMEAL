// composables/useCookbooksEditView.ts
import { useCookbookStore } from "~/stores/cookbooks/useCookbookStore";
import type { CookbookWritePayload } from "~/stores/cookbooks/useCookbookStore";
import { useRecipeStore } from "~/stores/useRecipeStore";
import { usePlanningStore } from "~/stores/usePlanningStore";
import { useToastStore } from "~/stores/useToastStore";
import { useAuth } from "~/composables/useAuth";
import { fileToDataUrl, isAllowedImageFile } from "~/composables/useRecipes";

export function useCookbookEditForm(props: {
  mode: "create" | "edit";
  cookbookId?: number;
}) {
  const store = useCookbookStore();
  const toast = useToastStore();

  const name = ref("");
  const icon = ref<string | null>(null);

  const isLoading = ref(props.mode === "edit");
  const isSaving = ref(false);
  const saveError = ref("");
  const savedNotice = ref(false);
  const deleteModalOpen = ref(false);
  const isDeleting = ref(false);

  const currentCookbook = computed(() => store.currentCookbook);

  const loadCookbook = async () => {
    if (props.mode !== "edit" || !props.cookbookId) return;
    isLoading.value = true;
    try {
      const cookbook = await store.fetchCookbook(props.cookbookId);
      name.value = cookbook.name;
      icon.value = cookbook.icon;
    } finally {
      isLoading.value = false;
    }
  };

  onMounted(loadCookbook);

  const onIconChange = async (event: Event) => {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    if (!isAllowedImageFile(file)) {
      toast.error("Format d'image non supporté. Utilisez un PNG, JPEG ou SVG.");
      input.value = "";
      return;
    }
    icon.value = await fileToDataUrl(file);
  };

  const validate = (): string | null => {
    if (!name.value.trim()) return "Le nom du cookbook est obligatoire.";
    return null;
  };

  const buildPayload = (): CookbookWritePayload => ({
    name: name.value.trim(),
    icon: icon.value || null,
  });

  const save = async () => {
    saveError.value = "";
    savedNotice.value = false;
    const error = validate();
    if (error) {
      saveError.value = error;
      return;
    }

    isSaving.value = true;
    try {
      const payload = buildPayload();
      if (props.mode === "create") {
        const cookbook = await store.createCookbook(payload);
        toast.success("Cookbook créé.");
        await navigateTo(`/cookbooks/${cookbook.id}/view`);
      } else if (props.cookbookId) {
        await store.updateCookbook(props.cookbookId, payload);
        savedNotice.value = true;
        toast.success("Cookbook enregistré.");
        setTimeout(() => (savedNotice.value = false), 2500);
      }
    } catch {
      saveError.value =
        "Impossible d'enregistrer le cookbook. Vérifiez les champs et réessayez.";
      toast.error(saveError.value);
    } finally {
      isSaving.value = false;
    }
  };

  const confirmDelete = async () => {
    if (!props.cookbookId || isDeleting.value) return;
    isDeleting.value = true;
    try {
      await store.deleteCookbook(props.cookbookId);
      deleteModalOpen.value = false;
      toast.success("Cookbook supprimé.");
      await navigateTo("/cookbooks");
    } catch {
      saveError.value = "Impossible de supprimer le cookbook.";
      toast.error(saveError.value);
      deleteModalOpen.value = false;
    } finally {
      isDeleting.value = false;
    }
  };

  return {
    name,
    icon,
    isLoading,
    isSaving,
    saveError,
    savedNotice,
    deleteModalOpen,
    isDeleting,
    currentCookbook,
    onIconChange,
    save,
    confirmDelete,
  };
}

export function useCookbookView(cookbookId: number) {
  const store = useCookbookStore();
  const recipeStore = useRecipeStore();
  const planningStore = usePlanningStore();
  const toast = useToastStore();
  const { user } = useAuth();

  const isLoading = ref(true);
  const deleteModalOpen = ref(false);
  const activeTab = ref<"recettes" | "planning">("recettes");

  const load = async () => {
    isLoading.value = true;
    try {
      const cookbook = await store.fetchCookbook(cookbookId);
      // Reuses the same recipe/planning stores as the personal list pages so
      // RecipeCard/PlanningCard's own favorite/delete actions (which mutate
      // those stores directly) stay in sync here for free.
      recipeStore.recipes = cookbook.recipes;
      planningStore.plannings = cookbook.plannings;
    } finally {
      isLoading.value = false;
    }
  };

  onMounted(load);

  const cookbook = computed(() => store.currentCookbook);
  const isOwner = computed(
    () => !!cookbook.value && cookbook.value.creator.id === user.value?.id,
  );

  const confirmDelete = async () => {
    try {
      await store.deleteCookbook(cookbookId);
      deleteModalOpen.value = false;
      toast.success("Cookbook supprimé.");
      await navigateTo("/cookbooks");
    } catch {
      toast.error("Impossible de supprimer le cookbook.");
      deleteModalOpen.value = false;
    }
  };

  return {
    isLoading,
    deleteModalOpen,
    activeTab,
    cookbook,
    isOwner,
    recipes: computed(() => recipeStore.recipes),
    plannings: computed(() => planningStore.plannings),
    confirmDelete,
  };
}
