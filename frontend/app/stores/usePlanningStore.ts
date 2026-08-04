// stores/usePlanningStore.ts
import { defineStore } from "pinia";
import { useApi } from "~/composables/useAPI";
import type { User } from "~/composables/useAuth";
import type { Recipe } from "~/stores/useRecipeStore";

export type PlanningType = "journalier" | "hebdomadaire";
export type MealMoment = "midi" | "soir";
export type MealCourse = "entree" | "plat" | "dessert";

export interface PlanningMeal {
  recipe: Recipe;
  type: MealCourse;
  lunch: MealMoment;
  dayofweek: string | null;
}

export interface Planning {
  id: number;
  name: string;
  icon: string | null;
  type: PlanningType;
  creator: User;
  cookbook: number | null;
  meals: PlanningMeal[];
  created_at: string;
  updated_at: string;
}

export interface MealInput {
  recipe: number;
  dayofweek: string;
  lunch: MealMoment;
  type: MealCourse;
}

export interface PlanningWritePayload {
  name: string;
  icon?: string | null;
  type?: PlanningType;
  cookbook?: number | null;
  meals?: MealInput[];
}

export interface PlanningListParams {
  name?: string;
  type?: PlanningType;
  cookbook?: string;
  in_cookbook?: boolean;
  shared_with_me?: boolean;
  page?: number;
  page_size?: number;
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

export const usePlanningStore = defineStore("plannings", () => {
  const { get, post, patch, del } = useApi();

  const plannings = ref<Planning[]>([]);
  const currentPlanning = ref<Planning | null>(null);
  const pagination = reactive({
    count: 0,
    total_pages: 0,
    current_page: 1,
    next: null as string | null,
    previous: null as string | null,
  });
  const loading = ref(false);
  const error = ref<string | null>(null);

  const fetchPlannings = async (
    params: PlanningListParams = {},
  ): Promise<Planning[]> => {
    loading.value = true;
    error.value = null;
    try {
      const response = await get<PaginatedResponse<Planning>>(
        `/plannings/${buildQuery(params)}`,
      );
      plannings.value = response.results;
      pagination.count = response.count;
      pagination.total_pages = response.total_pages;
      pagination.current_page = response.current_page;
      pagination.next = response.next;
      pagination.previous = response.previous;
      return response.results;
    } catch (cause) {
      error.value = "Impossible de charger les plannings.";
      throw cause;
    } finally {
      loading.value = false;
    }
  };

  const fetchPlanning = async (id: number): Promise<Planning> => {
    loading.value = true;
    error.value = null;
    try {
      const planning = await get<Planning>(`/plannings/${id}/`);
      currentPlanning.value = planning;
      return planning;
    } catch (cause) {
      error.value = "Impossible de charger le planning.";
      throw cause;
    } finally {
      loading.value = false;
    }
  };

  const createPlanning = async (
    payload: PlanningWritePayload,
  ): Promise<Planning> => {
    const planning = await post<Planning>(
      "/plannings/",
      payload as unknown as Record<string, unknown>,
    );
    plannings.value = [planning, ...plannings.value];
    currentPlanning.value = planning;
    return planning;
  };

  const updatePlanning = async (
    id: number,
    payload: Partial<PlanningWritePayload>,
  ): Promise<Planning> => {
    const planning = await patch<Planning>(
      `/plannings/${id}/`,
      payload as unknown as Record<string, unknown>,
    );
    plannings.value = plannings.value.map((p: Planning) =>
      p.id === id ? planning : p,
    );
    currentPlanning.value = planning;
    return planning;
  };

  const deletePlanning = async (id: number): Promise<void> => {
    await del(`/plannings/${id}/`);
    plannings.value = plannings.value.filter((p: Planning) => p.id !== id);
    if (currentPlanning.value?.id === id) currentPlanning.value = null;
  };

  return {
    plannings,
    currentPlanning,
    pagination,
    loading,
    error,
    fetchPlannings,
    fetchPlanning,
    createPlanning,
    updatePlanning,
    deletePlanning,
  };
});
