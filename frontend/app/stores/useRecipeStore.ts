// stores/useRecipeStore.ts
import { defineStore } from "pinia";
import { useApi } from "~/composables/useAPI";
import type { User } from "~/composables/useAuth";

export interface Ingredient {
  id: number;
  name: string;
  image: string | null;
  created_at: string;
  updated_at: string;
}

export interface Tag {
  id: number;
  name: string;
  type: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface Step {
  id: number;
  description: string;
  step_number: number;
  dury: string;
  type: string;
}

export interface RecipeIngredientLine {
  ingredient: Ingredient;
  quantity: string;
  unity: string | null;
  person_numbers: number;
}

export interface PlanningUsage {
  id: number;
  name: string;
}

export interface Recipe {
  id: number;
  title: string;
  image: string | null;
  source: string | null;
  cooking_duration: string | null;
  creator: User;
  cookbook: number | null;
  ingredients: RecipeIngredientLine[];
  tags: Tag[];
  steps: Step[];
  is_favorite: boolean;
  used_in_plannings: PlanningUsage[];
  created_at: string;
  updated_at: string;
}

export interface IngredientInput {
  name: string;
  image?: string | null;
  quantity: string | number;
  unity?: string | null;
  person_numbers: number;
}

export interface TagInput {
  name: string;
  type: string;
  description?: string | null;
}

export interface StepInput {
  description: string;
  step_number: number;
  dury: string;
  type: string;
}

export interface RecipeWritePayload {
  title: string;
  image?: string | null;
  source?: string | null;
  cooking_duration?: string | number | null;
  cookbook?: number | null;
  ingredients?: IngredientInput[];
  tags?: TagInput[];
  steps?: StepInput[];
}

export interface RecipeListParams {
  name?: string;
  tags?: string;
  ingredients?: string;
  cookbook?: string;
  in_cookbook?: boolean;
  favorite?: boolean;
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

export const useRecipeStore = defineStore("recipes", () => {
  const { get, post, patch, del } = useApi();

  const recipes = ref<Recipe[]>([]);
  const currentRecipe = ref<Recipe | null>(null);
  const tags = ref<Tag[]>([]);
  const ingredients = ref<Ingredient[]>([]);
  const pagination = reactive({
    count: 0,
    total_pages: 0,
    current_page: 1,
    next: null as string | null,
    previous: null as string | null,
  });
  const loading = ref(false);
  const error = ref<string | null>(null);

  const fetchRecipes = async (
    params: RecipeListParams = {},
  ): Promise<Recipe[]> => {
    loading.value = true;
    error.value = null;
    try {
      const response = await get<PaginatedResponse<Recipe>>(
        `/recipes/${buildQuery(params)}`,
      );
      recipes.value = response.results;
      pagination.count = response.count;
      pagination.total_pages = response.total_pages;
      pagination.current_page = response.current_page;
      pagination.next = response.next;
      pagination.previous = response.previous;
      return response.results;
    } catch (cause) {
      error.value = "Impossible de charger les recettes.";
      throw cause;
    } finally {
      loading.value = false;
    }
  };

  const fetchRecipe = async (id: number): Promise<Recipe> => {
    loading.value = true;
    error.value = null;
    try {
      const recipe = await get<Recipe>(`/recipes/${id}/`);
      currentRecipe.value = recipe;
      return recipe;
    } catch (cause) {
      error.value = "Impossible de charger la recette.";
      throw cause;
    } finally {
      loading.value = false;
    }
  };

  const createRecipe = async (payload: RecipeWritePayload): Promise<Recipe> => {
    const recipe = await post<Recipe>(
      "/recipes/",
      payload as unknown as Record<string, unknown>,
    );
    recipes.value = [recipe, ...recipes.value];
    currentRecipe.value = recipe;
    return recipe;
  };

  const updateRecipe = async (
    id: number,
    payload: Partial<RecipeWritePayload>,
  ): Promise<Recipe> => {
    const recipe = await patch<Recipe>(
      `/recipes/${id}/`,
      payload as unknown as Record<string, unknown>,
    );
    recipes.value = recipes.value.map((r: Recipe) =>
      r.id === id ? recipe : r,
    );
    currentRecipe.value = recipe;
    return recipe;
  };

  const deleteRecipe = async (id: number): Promise<void> => {
    await del(`/recipes/${id}/`);
    recipes.value = recipes.value.filter((r: Recipe) => r.id !== id);
    if (currentRecipe.value?.id === id) currentRecipe.value = null;
  };

  const setFavorite = async (id: number, favorite: boolean): Promise<void> => {
    if (favorite) {
      await post(`/recipes/${id}/favorite/`, {});
    } else {
      await del(`/recipes/${id}/favorite/`);
    }
    const patchLocal = (recipe: Recipe) =>
      recipe.id === id ? { ...recipe, is_favorite: favorite } : recipe;
    recipes.value = recipes.value.map(patchLocal);
    if (currentRecipe.value?.id === id) {
      currentRecipe.value = { ...currentRecipe.value, is_favorite: favorite };
    }
  };

  const fetchTags = async (search?: string): Promise<Tag[]> => {
    const result = await get<Tag[]>(`/tags/${buildQuery({ search })}`);
    tags.value = result;
    return result;
  };

  const fetchIngredients = async (search?: string): Promise<Ingredient[]> => {
    const result = await get<Ingredient[]>(
      `/ingredients/${buildQuery({ search })}`,
    );
    ingredients.value = result;
    return result;
  };

  return {
    recipes,
    currentRecipe,
    tags,
    ingredients,
    pagination,
    loading,
    error,
    fetchRecipes,
    fetchRecipe,
    createRecipe,
    updateRecipe,
    deleteRecipe,
    setFavorite,
    fetchTags,
    fetchIngredients,
  };
});
