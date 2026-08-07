// composables/useSearch.ts
import type { PlanningType } from "~/stores/usePlanningStore";

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
  };
}

export function createPlanningFilters(): PlanningFilterState {
  return { name: "", type: "", cookbookScope: "all", cookbookName: "" };
}

export function createCookbookFilters(): CookbookFilterState {
  return { name: "" };
}
