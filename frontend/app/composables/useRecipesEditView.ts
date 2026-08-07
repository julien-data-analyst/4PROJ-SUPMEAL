// composables/useRecipesEditView.ts
import { useRecipeStore } from "~/stores/useRecipeStore";
import type { RecipeWritePayload } from "~/stores/useRecipeStore";
import { useToastStore } from "~/stores/useToastStore";
import { useAuth } from "~/composables/useAuth";
import {
  useCookbookName,
  useCookbookRoleFor,
  COOKBOOK_ROLE_RANK,
} from "~/composables/useCookbooks";
import { useCookbookDiscussionContext } from "~/composables/useCookbookDiscussionContext";
import {
  emptyStepLine,
  fileToDataUrl,
  isAllowedImageFile,
  minutesToDury,
  recipeToIngredientLines,
  recipeToStepLines,
  recipeToTagLines,
  relativeTime,
  formatCookingDuration,
  sumStepMinutes,
  renderStepMarkdown,
  useRecipes,
} from "~/composables/useRecipes";
import type {
  IngredientLine,
  StepLine,
  TagLine,
} from "~/composables/useRecipes";

export function useRecipeEditForm(props: {
  mode: "create" | "edit";
  recipeId?: number;
}) {
  const store = useRecipeStore();
  const toast = useToastStore();
  const route = useRoute();

  // `store.currentRecipe` is a global singleton that otherwise keeps
  // pointing at whatever recipe was last viewed/edited until the fetch
  // below resolves - cleared synchronously here (not just in onMounted)
  // so the cookbookId/discussion-context watchers set up next never
  // briefly compute against a previous, unrelated recipe's cookbook.
  if (props.mode === "create" || store.currentRecipe?.id !== props.recipeId) {
    store.currentRecipe = null;
  }

  const title = ref("");
  const source = ref("");
  const cookingDuration = ref("");
  const image = ref<string | null>(null);

  const ingredientLines = ref<IngredientLine[]>([]);
  const tagLines = ref<TagLine[]>([]);
  const stepLines = ref<StepLine[]>([emptyStepLine()]);

  const previewMode = ref(false);
  const isLoading = ref(props.mode === "edit");
  const isSaving = ref(false);
  const saveError = ref("");
  const savedNotice = ref(false);
  const deleteModalOpen = ref(false);
  const isDeleting = ref(false);

  const currentRecipe = computed(() => store.currentRecipe);

  // A recipe is filed into a cookbook either because it already belongs to
  // one (edit mode, from the loaded recipe) or because it's being created
  // from within a cookbook's page (`/new?cookbook=<id>`).
  const cookbookIdParam = computed(() => {
    if (props.mode !== "create") return null;
    const raw = route.query.cookbook;
    const id = Number(Array.isArray(raw) ? raw[0] : raw);
    return Number.isFinite(id) && id > 0 ? id : null;
  });
  const cookbookId = computed(
    () => currentRecipe.value?.cookbook ?? cookbookIdParam.value,
  );
  const cookbookName = useCookbookName(() => cookbookId.value);

  const discussionContext = useCookbookDiscussionContext();
  watch(
    [cookbookId, currentRecipe],
    () => {
      discussionContext.value = cookbookId.value
        ? {
            cookbookId: cookbookId.value,
            default: currentRecipe.value
              ? { kind: "recipe", id: currentRecipe.value.id }
              : { kind: "general" },
          }
        : null;
    },
    { immediate: true },
  );

  // Live counter - sum of every step's own duration only (cooking_duration
  // is a separate, user-entered field and isn't part of this estimate).
  const totalMinutes = computed(() =>
    stepLines.value.reduce(
      (sum, s) => sum + (Number(s.durationMinutes) || 0),
      0,
    ),
  );

  const loadRecipe = async () => {
    if (props.mode !== "edit" || !props.recipeId) return;
    isLoading.value = true;
    try {
      const recipe = await store.fetchRecipe(props.recipeId);
      title.value = recipe.title;
      source.value = recipe.source ?? "";
      cookingDuration.value = recipe.cooking_duration ?? "";
      image.value = recipe.image;
      ingredientLines.value = recipeToIngredientLines(recipe);
      tagLines.value = recipeToTagLines(recipe);
      stepLines.value = recipeToStepLines(recipe).length
        ? recipeToStepLines(recipe)
        : [emptyStepLine()];
    } finally {
      isLoading.value = false;
    }
  };

  onMounted(loadRecipe);

  const onImageChange = async (event: Event) => {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    if (!isAllowedImageFile(file)) {
      toast.error("Format d'image non supporté. Utilisez un PNG, JPEG ou SVG.");
      input.value = "";
      return;
    }
    image.value = await fileToDataUrl(file);
  };

  const addStep = () => {
    stepLines.value = [...stepLines.value, emptyStepLine()];
  };

  const removeStep = (index: number) => {
    stepLines.value = stepLines.value.filter((_, i) => i !== index);
    if (!stepLines.value.length) stepLines.value = [emptyStepLine()];
  };

  const moveStep = (index: number, direction: -1 | 1) => {
    const target = index + direction;
    if (target < 0 || target >= stepLines.value.length) return;
    const next = [...stepLines.value];
    const [moved] = next.splice(index, 1);
    if (!moved) return;
    next.splice(target, 0, moved);
    stepLines.value = next;
  };

  const validate = (): string | null => {
    if (!title.value.trim()) return "Le titre de la recette est obligatoire.";

    const usedIngredientNames = new Set<string>();
    for (const line of ingredientLines.value) {
      if (!line.name.trim()) continue;
      if (!line.ingredientId && !line.image) {
        return `L'ingrédient « ${line.name} » est nouveau : une image est obligatoire.`;
      }
      if (!line.quantity || Number(line.quantity) <= 0) {
        return `Indiquez une quantité pour « ${line.name} ».`;
      }
      if (!line.personNumbers || Number(line.personNumbers) < 1) {
        return `Indiquez un nombre de personnes pour « ${line.name} ».`;
      }
      const key = line.name.trim().toLowerCase();
      if (usedIngredientNames.has(key)) {
        return `L'ingrédient « ${line.name} » est ajouté plusieurs fois.`;
      }
      usedIngredientNames.add(key);
    }

    const usedTagNames = new Set<string>();
    for (const tag of tagLines.value) {
      if (!tag.name.trim()) continue;
      const key = tag.name.trim().toLowerCase();
      if (usedTagNames.has(key)) {
        return `Le tag « ${tag.name} » est ajouté plusieurs fois.`;
      }
      usedTagNames.add(key);
    }

    return null;
  };

  const buildPayload = (): RecipeWritePayload => ({
    title: title.value.trim(),
    image: image.value || null,
    source: source.value.trim() || null,
    cooking_duration: cookingDuration.value
      ? Number(cookingDuration.value)
      : null,
    ...(cookbookIdParam.value ? { cookbook: cookbookIdParam.value } : {}),
    ingredients: ingredientLines.value
      .filter((l) => l.name.trim())
      .map((l) => ({
        name: l.name.trim(),
        image: l.image || null,
        quantity: Number(l.quantity) || 0,
        unity: l.unity.trim() || null,
        person_numbers: Number(l.personNumbers) || 1,
      })),
    tags: tagLines.value
      .filter((t) => t.name.trim())
      .map((t) => ({
        name: t.name.trim(),
        type: t.type,
        description: t.description.trim() || null,
      })),
    steps: stepLines.value
      .filter((s) => s.description.trim())
      .map((s, i) => ({
        description: s.description,
        step_number: i + 1,
        dury: minutesToDury(s.durationMinutes),
        type: s.type,
      })),
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
        const recipe = await store.createRecipe(payload);
        toast.success("Recette créée.");
        // Replaces this "create" entry so "Retour" from the edit page that
        // follows lands on whatever page the user was on before creating
        // the recipe, not back onto a blank creation form.
        await navigateTo(`/recipes/${recipe.id}/edit`, { replace: true });
      } else if (props.recipeId) {
        await store.updateRecipe(props.recipeId, payload);
        savedNotice.value = true;
        toast.success("Recette enregistrée.");
        setTimeout(() => (savedNotice.value = false), 2500);
      }
    } catch {
      saveError.value =
        "Impossible d'enregistrer la recette. Vérifiez les champs et réessayez.";
      toast.error(saveError.value);
    } finally {
      isSaving.value = false;
    }
  };

  const confirmDelete = async () => {
    if (!props.recipeId || isDeleting.value) return;
    isDeleting.value = true;
    try {
      await store.deleteRecipe(props.recipeId);
      deleteModalOpen.value = false;
      toast.success("Recette supprimée.");
      await navigateTo("/recipes");
    } catch {
      saveError.value = "Impossible de supprimer la recette.";
      toast.error(saveError.value);
      deleteModalOpen.value = false;
    } finally {
      isDeleting.value = false;
    }
  };

  return {
    title,
    source,
    cookingDuration,
    image,
    ingredientLines,
    tagLines,
    stepLines,
    previewMode,
    isLoading,
    isSaving,
    saveError,
    savedNotice,
    deleteModalOpen,
    isDeleting,
    currentRecipe,
    cookbookId,
    cookbookName,
    totalMinutes,
    onImageChange,
    addStep,
    removeStep,
    moveStep,
    save,
    confirmDelete,
    relativeTime,
    formatCookingDuration,
  };
}

export function useRecipeView(recipeId: number) {
  const store = useRecipeStore();
  const toast = useToastStore();
  const { toggleFavorite } = useRecipes();
  const { user } = useAuth();

  // See the identical guard in useRecipeEditForm - avoids a stale
  // previously-viewed recipe leaking into the computeds below.
  if (store.currentRecipe?.id !== recipeId) {
    store.currentRecipe = null;
  }

  const isLoading = ref(true);
  const deleteModalOpen = ref(false);

  onMounted(async () => {
    isLoading.value = true;
    try {
      await store.fetchRecipe(recipeId);
    } finally {
      isLoading.value = false;
    }
  });

  const recipe = computed(() => store.currentRecipe);
  const isOwner = computed(
    () => !!recipe.value && recipe.value.creator.id === user.value?.id,
  );
  const totalPrepMinutes = computed(() =>
    recipe.value ? sumStepMinutes(recipe.value.steps) : 0,
  );
  const cookbookName = useCookbookName(() => recipe.value?.cookbook ?? null);
  const cookbookRole = useCookbookRoleFor(() => recipe.value?.cookbook ?? null);

  const discussionContext = useCookbookDiscussionContext();
  watch(
    recipe,
    (r) => {
      discussionContext.value = r?.cookbook
        ? { cookbookId: r.cookbook, default: { kind: "recipe", id: r.id } }
        : null;
    },
    { immediate: true },
  );
  // A shared cookbook member who didn't create this recipe can still edit
  // (editor rank+) or delete (creator rank+) it - mirrors the backend's
  // CookbookItemPermission.
  const canEdit = computed(
    () =>
      isOwner.value ||
      (!!cookbookRole.value &&
        COOKBOOK_ROLE_RANK[cookbookRole.value] >= COOKBOOK_ROLE_RANK.editor),
  );
  const canManage = computed(
    () =>
      isOwner.value ||
      (!!cookbookRole.value &&
        COOKBOOK_ROLE_RANK[cookbookRole.value] >= COOKBOOK_ROLE_RANK.creator),
  );

  const onToggleFavorite = async () => {
    if (!recipe.value) return;
    const nowFavorite = !recipe.value.is_favorite;
    try {
      await toggleFavorite(recipe.value);
      toast.success(
        nowFavorite ? "Ajouté aux favoris." : "Retiré des favoris.",
      );
    } catch {
      toast.error("Impossible de mettre à jour les favoris.");
    }
  };

  const confirmDelete = async () => {
    try {
      await store.deleteRecipe(recipeId);
      deleteModalOpen.value = false;
      toast.success("Recette supprimée.");
      await navigateTo("/recipes");
    } catch {
      toast.error("Impossible de supprimer la recette.");
      deleteModalOpen.value = false;
    }
  };

  return {
    isLoading,
    deleteModalOpen,
    recipe,
    isOwner,
    canEdit,
    canManage,
    totalPrepMinutes,
    cookbookName,
    onToggleFavorite,
    confirmDelete,
    formatCookingDuration,
    renderStepMarkdown,
  };
}
