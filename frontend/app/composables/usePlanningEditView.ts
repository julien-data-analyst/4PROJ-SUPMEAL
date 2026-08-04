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
  const toast = useToastStore();

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
        await navigateTo(`/planning/${planning.id}/edit`);
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
    mealsMap,
    confirmDelete,
  };
}
