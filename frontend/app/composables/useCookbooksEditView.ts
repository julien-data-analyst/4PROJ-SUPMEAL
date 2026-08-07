// composables/useCookbooksEditView.ts
import { useCookbookStore } from "~/stores/cookbooks/useCookbookStore";
import type { CookbookWritePayload } from "~/stores/cookbooks/useCookbookStore";
import { useRecipeStore } from "~/stores/useRecipeStore";
import { usePlanningStore } from "~/stores/usePlanningStore";
import { useToastStore } from "~/stores/useToastStore";
import { useAuth } from "~/composables/useAuth";
import { fileToDataUrl, isAllowedImageFile } from "~/composables/useRecipes";
import { getCookbookRole, hasCookbookRank } from "~/composables/useCookbooks";
import { useCookbookDiscussionContext } from "~/composables/useCookbookDiscussionContext";

export interface DeleteCookbookOptions {
  keepRecipes: boolean;
  keepPlannings: boolean;
}

// Deleting a cookbook is a plain `DELETE /cookbooks/{id}/`, which already
// reverts any *remaining* recipes/plannings to personal (see the backend's
// `CookbookViewSet.perform_destroy`). "Don't keep" is handled here, up
// front, by deleting those recipes/plannings first via their own existing
// endpoints (each already knows how to clean up its own references, e.g. a
// recipe used in a planning) - no dedicated backend route needed. Plannings
// are removed before recipes so a still-live planning never briefly points
// at an already-deleted recipe.
export async function deleteCookbookWithOptions(
  cookbookId: number,
  recipes: { id: number }[],
  plannings: { id: number }[],
  options: DeleteCookbookOptions,
): Promise<void> {
  const cookbookStore = useCookbookStore();
  const recipeStore = useRecipeStore();
  const planningStore = usePlanningStore();

  if (!options.keepPlannings) {
    for (const planning of plannings) {
      await planningStore.deletePlanning(planning.id);
    }
  }
  if (!options.keepRecipes) {
    for (const recipe of recipes) {
      await recipeStore.deleteRecipe(recipe.id);
    }
  }
  await cookbookStore.deleteCookbook(cookbookId);
}

export function useCookbookEditForm(props: {
  mode: "create" | "edit";
  cookbookId?: number;
}) {
  const store = useCookbookStore();
  const toast = useToastStore();

  // `store.currentCookbook` is a global singleton that otherwise keeps
  // pointing at whatever cookbook was last viewed/edited until the fetch
  // below resolves - cleared synchronously here so nothing reads a
  // previous, unrelated cookbook's data in the meantime.
  if (
    props.mode === "create" ||
    store.currentCookbook?.id !== props.cookbookId
  ) {
    store.currentCookbook = null;
  }

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
        // Replaces this "create" entry so "Retour" from the view page that
        // follows lands on whatever page the user was on before creating
        // the cookbook, not back onto a blank creation form.
        await navigateTo(`/cookbooks/${cookbook.id}/view`, { replace: true });
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

  const confirmDelete = async (options: DeleteCookbookOptions) => {
    if (!props.cookbookId || isDeleting.value) return;
    isDeleting.value = true;
    try {
      await deleteCookbookWithOptions(
        props.cookbookId,
        currentCookbook.value?.recipes ?? [],
        currentCookbook.value?.plannings ?? [],
        options,
      );
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
  const discussionContext = useCookbookDiscussionContext();

  // See the identical guard in useCookbookEditForm - the page's header
  // action row (Modifier/Supprimer) checks `isOwner` before `isLoading`
  // gates the rest of the page, so a stale cookbook here could otherwise
  // flash the wrong owner's controls for an instant.
  if (store.currentCookbook?.id !== cookbookId) {
    store.currentCookbook = null;
  }

  const isLoading = ref(true);
  const deleteModalOpen = ref(false);
  const activeTab = ref<"recettes" | "planning" | "membres">("recettes");

  const load = async () => {
    isLoading.value = true;
    try {
      const cookbook = await store.fetchCookbook(cookbookId);
      // Reuses the same recipe/planning stores as the personal list pages so
      // RecipeCard/PlanningCard's own favorite/delete actions (which mutate
      // those stores directly) stay in sync here for free.
      recipeStore.recipes = cookbook.recipes;
      planningStore.plannings = cookbook.plannings;
      discussionContext.value = { cookbookId, default: { kind: "general" } };
    } finally {
      isLoading.value = false;
    }
  };

  onMounted(load);

  const cookbook = computed(() => store.currentCookbook);
  const isOwner = computed(
    () => !!cookbook.value && cookbook.value.creator.id === user.value?.id,
  );
  const myRole = computed(() =>
    cookbook.value ? getCookbookRole(cookbook.value, user.value?.id) : null,
  );
  // "creator" role and up can file new recipes/plannings into the cookbook
  // (see the backend's `validate_cookbook` on both write serializers);
  // below that (reader/commentator/editor), only viewing/editing existing
  // content is allowed.
  const canManageContent = computed(
    () =>
      !!cookbook.value &&
      hasCookbookRank(cookbook.value, user.value?.id, "creator"),
  );
  const canEditContent = computed(
    () =>
      !!cookbook.value &&
      hasCookbookRank(cookbook.value, user.value?.id, "editor"),
  );

  const confirmDelete = async (options: DeleteCookbookOptions) => {
    try {
      // Uses the live store lists (not `cookbook.value.recipes/plannings`,
      // a snapshot from the initial load) so a recipe/planning removed or
      // reassigned since then via its own card isn't deleted a second time.
      await deleteCookbookWithOptions(
        cookbookId,
        recipeStore.recipes,
        planningStore.plannings,
        options,
      );
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
    myRole,
    canManageContent,
    canEditContent,
    recipes: computed(() => recipeStore.recipes),
    plannings: computed(() => planningStore.plannings),
    confirmDelete,
  };
}
