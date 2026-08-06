// composables/usePlanningEditView.ts
import { usePlanningStore } from "~/stores/usePlanningStore";
import type {
  PlanningWritePayload,
  PlanningType,
} from "~/stores/usePlanningStore";
import { useToastStore } from "~/stores/useToastStore";
import { useAuth } from "~/composables/useAuth";
import { fileToDataUrl, isAllowedImageFile } from "~/composables/useRecipes";
import {
  generateEmptySlots,
  planningToMealSlots,
  mealsByDayAndSlot,
} from "~/composables/usePlanning";
import type { MealSlot } from "~/composables/usePlanning";
import { useCookbookStore } from "~/stores/cookbooks/useCookbookStore";
import {
  useCookbookName,
  useCookbookRoleFor,
  COOKBOOK_ROLE_RANK,
} from "~/composables/useCookbooks";
import type { Recipe } from "~/stores/useRecipeStore";
import { useCookbookDiscussionContext } from "~/composables/useCookbookDiscussionContext";

export interface RecipePick {
  id: number | null;
  title: string;
  image: string | null;
}

export function usePlanningEditForm(props: {
  mode: "create" | "edit";
  planningId?: number;
}) {
  const store = usePlanningStore();
  const cookbookStore = useCookbookStore();
  const toast = useToastStore();
  const route = useRoute();

  // `store.currentPlanning` is a global singleton that otherwise keeps
  // pointing at whatever planning was last viewed/edited until the fetch
  // below resolves - cleared synchronously here (not just in onMounted)
  // so the cookbookId/discussion-context watchers set up next never
  // briefly compute against a previous, unrelated planning's cookbook.
  if (
    props.mode === "create" ||
    store.currentPlanning?.id !== props.planningId
  ) {
    store.currentPlanning = null;
  }

  const name = ref("");
  const icon = ref<string | null>(null);
  const type = ref<PlanningType>("hebdomadaire");
  const slots = ref<MealSlot[]>(generateEmptySlots(type.value));

  const isLoading = ref(props.mode === "edit");
  const isSaving = ref(false);
  const saveError = ref("");
  const savedNotice = ref(false);
  const deleteModalOpen = ref(false);
  const isDeleting = ref(false);

  const currentPlanning = computed(() => store.currentPlanning);

  const scheduledCount = computed(
    () => slots.value.filter((s) => s.recipeId !== null).length,
  );

  // A planning is filed into a cookbook either because it already belongs
  // to one (edit mode, from the loaded planning) or because it's being
  // created from within a cookbook's page (`/planning/new?cookbook=<id>`).
  const cookbookIdParam = computed(() => {
    if (props.mode !== "create") return null;
    const raw = route.query.cookbook;
    const id = Number(Array.isArray(raw) ? raw[0] : raw);
    return Number.isFinite(id) && id > 0 ? id : null;
  });
  const cookbookId = computed(
    () => currentPlanning.value?.cookbook ?? cookbookIdParam.value,
  );
  const cookbookName = useCookbookName(() => cookbookId.value);

  const discussionContext = useCookbookDiscussionContext();
  watch(
    [cookbookId, currentPlanning],
    () => {
      discussionContext.value = cookbookId.value
        ? {
            cookbookId: cookbookId.value,
            default: currentPlanning.value
              ? { kind: "planning", id: currentPlanning.value.id }
              : { kind: "general" },
          }
        : null;
    },
    { immediate: true },
  );

  // A cookbook-scoped planning can only schedule recipes that belong to the
  // same cookbook, so the recipe picker's suggestions are restricted to this
  // list instead of searching the user's personal recipes.
  const cookbookRecipes = ref<Recipe[]>([]);
  watch(
    cookbookId,
    async (id) => {
      if (!id) {
        cookbookRecipes.value = [];
        return;
      }
      const cookbook = await cookbookStore.fetchCookbook(id);
      cookbookRecipes.value = cookbook.recipes;
    },
    { immediate: true },
  );

  const loadPlanning = async () => {
    if (props.mode !== "edit" || !props.planningId) return;
    isLoading.value = true;
    try {
      const planning = await store.fetchPlanning(props.planningId);
      name.value = planning.name;
      icon.value = planning.icon;
      type.value = planning.type;
      slots.value = planningToMealSlots(planning);
    } finally {
      isLoading.value = false;
    }
  };

  onMounted(loadPlanning);

  // Only meaningful before any meal is scheduled - switching type once the
  // grid is defined would silently drop the day/moment shape of every slot
  // already filled, so the type selector is create-mode only (see the
  // editor's template).
  const onTypeChange = (event: Event) => {
    const newType = (event.target as HTMLSelectElement).value as PlanningType;
    type.value = newType;
    slots.value = generateEmptySlots(newType);
  };

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

  const setSlotRecipe = (key: string, pick: RecipePick) => {
    slots.value = slots.value.map((s) =>
      s.key === key
        ? {
            ...s,
            recipeId: pick.id,
            recipeTitle: pick.title,
            recipeImage: pick.image,
          }
        : s,
    );
  };

  const validate = (): string | null => {
    if (!name.value.trim()) return "Le nom du planning est obligatoire.";
    return null;
  };

  const buildPayload = (): PlanningWritePayload => ({
    name: name.value.trim(),
    icon: icon.value || null,
    type: type.value,
    ...(cookbookIdParam.value ? { cookbook: cookbookIdParam.value } : {}),
    meals: slots.value
      .filter((s) => s.recipeId !== null)
      .map((s) => ({
        recipe: s.recipeId as number,
        dayofweek: s.dayofweek,
        lunch: s.lunch,
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
        const planning = await store.createPlanning(payload);
        toast.success("Planning créé.");
        // Replaces this "create" entry so "Retour" from the edit page that
        // follows lands on whatever page the user was on before creating
        // the planning, not back onto a blank creation form.
        await navigateTo(`/planning/${planning.id}/edit`, { replace: true });
      } else if (props.planningId) {
        await store.updatePlanning(props.planningId, payload);
        savedNotice.value = true;
        toast.success("Planning enregistré.");
        setTimeout(() => (savedNotice.value = false), 2500);
      }
    } catch {
      saveError.value =
        "Impossible d'enregistrer le planning. Vérifiez les champs et réessayez.";
      toast.error(saveError.value);
    } finally {
      isSaving.value = false;
    }
  };

  const confirmDelete = async () => {
    if (!props.planningId || isDeleting.value) return;
    isDeleting.value = true;
    try {
      await store.deletePlanning(props.planningId);
      deleteModalOpen.value = false;
      toast.success("Planning supprimé.");
      await navigateTo("/planning");
    } catch {
      saveError.value = "Impossible de supprimer le planning.";
      toast.error(saveError.value);
      deleteModalOpen.value = false;
    } finally {
      isDeleting.value = false;
    }
  };

  return {
    name,
    icon,
    type,
    slots,
    isLoading,
    isSaving,
    saveError,
    savedNotice,
    deleteModalOpen,
    isDeleting,
    currentPlanning,
    cookbookId,
    cookbookName,
    cookbookRecipes,
    scheduledCount,
    onTypeChange,
    onIconChange,
    setSlotRecipe,
    save,
    confirmDelete,
  };
}

export function usePlanningView(planningId: number) {
  const store = usePlanningStore();
  const toast = useToastStore();
  const { user } = useAuth();

  // See the identical guard in usePlanningEditForm - avoids a stale
  // previously-viewed planning leaking into the computeds below.
  if (store.currentPlanning?.id !== planningId) {
    store.currentPlanning = null;
  }

  const isLoading = ref(true);
  const deleteModalOpen = ref(false);

  onMounted(async () => {
    isLoading.value = true;
    try {
      await store.fetchPlanning(planningId);
    } finally {
      isLoading.value = false;
    }
  });

  const planning = computed(() => store.currentPlanning);
  const isOwner = computed(
    () => !!planning.value && planning.value.creator.id === user.value?.id,
  );
  const mealsMap = computed(() =>
    planning.value ? mealsByDayAndSlot(planning.value.meals) : new Map(),
  );
  const cookbookName = useCookbookName(() => planning.value?.cookbook ?? null);
  const cookbookRole = useCookbookRoleFor(
    () => planning.value?.cookbook ?? null,
  );

  const discussionContext = useCookbookDiscussionContext();
  watch(
    planning,
    (p) => {
      discussionContext.value = p?.cookbook
        ? { cookbookId: p.cookbook, default: { kind: "planning", id: p.id } }
        : null;
    },
    { immediate: true },
  );
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

  const confirmDelete = async () => {
    try {
      await store.deletePlanning(planningId);
      deleteModalOpen.value = false;
      toast.success("Planning supprimé.");
      await navigateTo("/planning");
    } catch {
      toast.error("Impossible de supprimer le planning.");
      deleteModalOpen.value = false;
    }
  };

  return {
    isLoading,
    deleteModalOpen,
    planning,
    isOwner,
    canEdit,
    canManage,
    mealsMap,
    cookbookName,
    confirmDelete,
  };
}
