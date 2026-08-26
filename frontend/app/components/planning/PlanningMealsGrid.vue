<script setup lang="ts">
import type { PlanningMeal, PlanningType } from "~/stores/usePlanningStore";
import {
  DAYS_OF_WEEK,
  MEAL_MOMENTS,
  MEAL_COURSES,
  DAILY_PLANNING_DAY,
  mealsByDayAndSlot,
} from "~/composables/usePlanning";
import type { DayOption } from "~/composables/usePlanning";
import IconRecipe from "~/components/icons/IconRecipe.vue";

const props = defineProps<{ type: PlanningType; meals: PlanningMeal[] }>();

const days = computed<DayOption[]>(() =>
  props.type === "journalier"
    ? [{ value: DAILY_PLANNING_DAY, label: "Repas" }]
    : DAYS_OF_WEEK,
);

// Pre-resolves every cell's meal once so the template doesn't repeat the
// same map lookup 4x per cell.
const grid = computed(() => {
  const mealsMap = mealsByDayAndSlot(props.meals);
  return MEAL_MOMENTS.map((moment) => ({
    moment,
    rows: MEAL_COURSES.map((course) => ({
      course,
      cells: days.value.map((day) => ({
        key: day.value,
        meal: mealsMap.get(`${day.value}-${moment.value}-${course.value}`),
      })),
    })),
  }));
});
</script>

<template>
  <div class="flex flex-col gap-8">
    <div v-for="block in grid" :key="block.moment.value">
      <p class="mb-3 text-[14px] font-bold text-sup-dark-green">
        {{ block.moment.label }}
      </p>
      <div class="overflow-x-auto rounded-md border border-sup-border">
        <table class="w-full border-collapse text-left text-[13.5px]">
          <thead>
            <tr class="bg-sup-light-gray">
              <th class="w-24 px-3 py-3 font-semibold text-gray-400"></th>
              <th
                v-for="day in days"
                :key="day.value"
                class="min-w-[210px] px-3 py-3 font-semibold text-sup-very-gray"
              >
                {{ day.label }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in block.rows"
              :key="row.course.value"
              class="border-t border-sup-border"
            >
              <td class="px-3 py-3 align-middle font-semibold text-gray-400">
                {{ row.course.label }}
              </td>
              <td
                v-for="cell in row.cells"
                :key="cell.key"
                class="px-3 py-3 align-middle"
              >
                <NuxtLink
                  v-if="cell.meal"
                  :to="`/recipes/${cell.meal.recipe.id}/view`"
                  :title="cell.meal.recipe.title"
                  class="flex min-h-[52px] items-center gap-2.5 rounded-md border border-sup-border bg-sup-withe px-3 py-2.5 hover:border-sup-dark-green hover:bg-sup-light-green/10"
                >
                  <img
                    v-if="cell.meal.recipe.image"
                    :src="cell.meal.recipe.image"
                    class="h-9 w-9 shrink-0 rounded object-cover"
                  />
                  <IconRecipe v-else size="sm" class="shrink-0 text-gray-400" />
                  <span class="truncate text-sup-very-gray">
                    {{ cell.meal.recipe.title }}
                  </span>
                </NuxtLink>
                <div
                  v-else
                  class="flex min-h-[52px] items-center justify-center rounded-md border border-dashed border-sup-border/70 text-gray-300"
                >
                  —
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
