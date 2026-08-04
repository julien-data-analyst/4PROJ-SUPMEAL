// composables/usePlanning.ts
import { usePlanningStore } from "~/stores/usePlanningStore";
import type {
  Planning,
  PlanningMeal,
  PlanningType,
  MealMoment,
  MealCourse,
} from "~/stores/usePlanningStore";

export interface DayOption {
  value: string;
  label: string;
}

export const DAYS_OF_WEEK: DayOption[] = [
  { value: "lundi", label: "Lundi" },
  { value: "mardi", label: "Mardi" },
  { value: "mercredi", label: "Mercredi" },
  { value: "jeudi", label: "Jeudi" },
  { value: "vendredi", label: "Vendredi" },
  { value: "samedi", label: "Samedi" },
  { value: "dimanche", label: "Dimanche" },
];

export const MEAL_MOMENTS: { value: MealMoment; label: string }[] = [
  { value: "midi", label: "Midi" },
  { value: "soir", label: "Soir" },
];

export const MEAL_COURSES: { value: MealCourse; label: string }[] = [
  { value: "entree", label: "Entrée" },
  { value: "plat", label: "Plat" },
  { value: "dessert", label: "Dessert" },
];

export const PLANNING_TYPE_LABELS: Record<PlanningType, string> = {
  journalier: "Journalier",
  hebdomadaire: "Hebdomadaire",
};

// Day-of-week is meaningless for a single-day plan, but the
// (planning, dayofweek, lunch, type) slot still requires one to stay
// unique - every "journalier" meal is pinned to this sentinel day.
export const DAILY_PLANNING_DAY = "lundi";

let slotUidCounter = 0;
export function slotUid(prefix = "slot"): string {
  slotUidCounter += 1;
  return `${prefix}-${Date.now()}-${slotUidCounter}`;
}

export interface MealSlot {
  key: string;
  dayofweek: string;
  lunch: MealMoment;
  type: MealCourse;
  recipeId: number | null;
  recipeTitle: string;
  recipeImage: string | null;
}

// Builds every schedulable slot for a planning type: 6 for a single day
// (2 moments x 3 courses), 42 for the week (7 days x 2 moments x 3 courses).
export function generateEmptySlots(type: PlanningType): MealSlot[] {
  const days =
    type === "journalier"
      ? [DAILY_PLANNING_DAY]
      : DAYS_OF_WEEK.map((d) => d.value);
  const slots: MealSlot[] = [];
  for (const day of days) {
    for (const moment of MEAL_MOMENTS) {
      for (const course of MEAL_COURSES) {
        slots.push({
          key: slotUid(),
          dayofweek: day,
          lunch: moment.value,
          type: course.value,
          recipeId: null,
          recipeTitle: "",
          recipeImage: null,
        });
      }
    }
  }
  return slots;
}

// Fills the empty grid for `planning.type` with whichever slots the
// planning already has a recipe scheduled for.
export function planningToMealSlots(planning: Planning): MealSlot[] {
  const slots = generateEmptySlots(planning.type);
  for (const meal of planning.meals) {
    const slot = slots.find(
      (s) =>
        s.dayofweek === meal.dayofweek &&
        s.lunch === meal.lunch &&
        s.type === meal.type,
    );
    if (slot) {
      slot.recipeId = meal.recipe.id;
      slot.recipeTitle = meal.recipe.title;
      slot.recipeImage = meal.recipe.image;
    }
  }
  return slots;
}

export function mealsByDayAndSlot(
  meals: PlanningMeal[],
): Map<string, PlanningMeal> {
  const map = new Map<string, PlanningMeal>();
  for (const meal of meals) {
    map.set(`${meal.dayofweek}-${meal.lunch}-${meal.type}`, meal);
  }
  return map;
}

export function usePlanning() {
  const store = usePlanningStore();

  const fetchMyPlannings = (search = "") =>
    store.fetchPlannings({ in_cookbook: false, name: search || undefined });

  const fetchRecentPlannings = async (limit = 3): Promise<void> => {
    await store.fetchPlannings({
      in_cookbook: false,
      page_size: limit,
    });
  };

  return {
    store,
    fetchMyPlannings,
    fetchRecentPlannings,
  };
}
