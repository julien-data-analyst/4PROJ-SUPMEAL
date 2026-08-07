// composables/useSearch.ts
import type { Planning, PlanningType } from "~/stores/usePlanningStore";
import type { Recipe } from "~/stores/useRecipeStore";
import { sumStepMinutes } from "~/composables/useRecipes";

export type SearchType = "recipes" | "plannings" | "cookbooks";

// "all": no restriction. "personal"/"not_planned": excluded from any
// cookbook/planning. "cookbook"/"planned": filed in one, optionally
// narrowed by its name.
export type CookbookScope = "all" | "personal" | "cookbook";
export type PlanningScope = "all" | "not_planned" | "planned";
export type FavoriteScope = "all" | "favorite" | "not_favorite";

export interface RecipeFilterState {
  name: string;
  ingredients: string;
  tags: string;
  cookbookScope: CookbookScope;
  cookbookName: string;
  planningScope: PlanningScope;
  planningName: string;
  favoriteScope: FavoriteScope;
  // Frontend-only: narrows the currently loaded recipes by prep/cooking
  // time (minutes), never sent to the backend.
  prepTimeMin: number | "";
  prepTimeMax: number | "";
  cookingTimeMin: number | "";
  cookingTimeMax: number | "";
}

export interface PlanningFilterState {
  name: string;
  type: "" | PlanningType;
  cookbookScope: CookbookScope;
  cookbookName: string;
}

export interface CookbookFilterState {
  name: string;
}

export function createRecipeFilters(): RecipeFilterState {
  return {
    name: "",
    ingredients: "",
    tags: "",
    cookbookScope: "all",
    cookbookName: "",
    planningScope: "all",
    planningName: "",
    favoriteScope: "all",
    prepTimeMin: "",
    prepTimeMax: "",
    cookingTimeMin: "",
    cookingTimeMax: "",
  };
}

export function createPlanningFilters(): PlanningFilterState {
  return { name: "", type: "", cookbookScope: "all", cookbookName: "" };
}

export function createCookbookFilters(): CookbookFilterState {
  return { name: "" };
}

// Fully client-side equivalent of the backend's recipe filters, applied
// against an already-loaded (unpaginated) array - used by a cookbook's own
// "Recettes" tab, which reuses <SearchFilters> but has no backend query to
// delegate to since `cookbook.recipes` is loaded in full up front.
// `cookbookScope`/`cookbookName` are ignored: everything passed in is
// already scoped to one specific cookbook.
export function filterRecipesLocally(
  recipes: Recipe[],
  f: RecipeFilterState,
): Recipe[] {
  const nameNeedle = f.name.trim().toLowerCase();
  const tagNeedles = f.tags
    .split(",")
    .map((t) => t.trim().toLowerCase())
    .filter(Boolean);
  const ingredientNeedles = f.ingredients
    .split(",")
    .map((t) => t.trim().toLowerCase())
    .filter(Boolean);

  return recipes.filter((recipe) => {
    if (nameNeedle && !recipe.title.toLowerCase().includes(nameNeedle))
      return false;

    if (tagNeedles.length) {
      const names = recipe.tags.map((t) => t.name.toLowerCase());
      if (!tagNeedles.every((needle) => names.some((n) => n.includes(needle))))
        return false;
    }

    if (ingredientNeedles.length) {
      const names = recipe.ingredients.map((l) =>
        l.ingredient.name.toLowerCase(),
      );
      if (
        !ingredientNeedles.every((needle) =>
          names.some((n) => n.includes(needle)),
        )
      )
        return false;
    }

    if (f.planningScope !== "all") {
      const inPlanning = recipe.used_in_plannings.length > 0;
      if (f.planningScope === "planned" && !inPlanning) return false;
      if (f.planningScope === "not_planned" && inPlanning) return false;
    }

    if (f.favoriteScope !== "all") {
      if (f.favoriteScope === "favorite" && !recipe.is_favorite) return false;
      if (f.favoriteScope === "not_favorite" && recipe.is_favorite)
        return false;
    }

    if (f.prepTimeMin !== "" || f.prepTimeMax !== "") {
      const prepMinutes = sumStepMinutes(recipe.steps);
      if (f.prepTimeMin !== "" && prepMinutes < f.prepTimeMin) return false;
      if (f.prepTimeMax !== "" && prepMinutes > f.prepTimeMax) return false;
    }

    if (f.cookingTimeMin !== "" || f.cookingTimeMax !== "") {
      const cookingMinutes =
        recipe.cooking_duration !== null
          ? Number(recipe.cooking_duration)
          : null;
      if (
        f.cookingTimeMin !== "" &&
        (cookingMinutes === null || cookingMinutes < f.cookingTimeMin)
      )
        return false;
      if (
        f.cookingTimeMax !== "" &&
        (cookingMinutes === null || cookingMinutes > f.cookingTimeMax)
      )
        return false;
    }

    return true;
  });
}

// Same idea as `filterRecipesLocally`, for a cookbook's "Planning" tab.
// `cookbookScope`/`cookbookName` ignored for the same reason.
export function filterPlanningsLocally(
  plannings: Planning[],
  f: PlanningFilterState,
): Planning[] {
  const nameNeedle = f.name.trim().toLowerCase();
  return plannings.filter((planning) => {
    if (nameNeedle && !planning.name.toLowerCase().includes(nameNeedle))
      return false;
    if (f.type && planning.type !== f.type) return false;
    return true;
  });
}
