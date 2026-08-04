<script setup lang="ts">
import type { PlanningType } from "~/stores/usePlanningStore";
import type { MealSlot } from "~/composables/usePlanning";
import {
  DAYS_OF_WEEK,
  MEAL_MOMENTS,
  MEAL_COURSES,
  DAILY_PLANNING_DAY,
} from "~/composables/usePlanning";
import type { RecipePick } from "~/composables/usePlanningEditView";
import RecipePicker from "~/components/planning/RecipePicker.vue";

const props = defineProps<{ type: PlanningType; slots: MealSlot[] }>();
const emit = defineEmits<{ "update-slot": [key: string, pick: RecipePick] }>();

const days = computed(() =>
  props.type === "journalier"
    ? [{ value: DAILY_PLANNING_DAY, label: "Repas" }]
    : DAYS_OF_WEEK,
);

const slotFor = (day: string, moment: string, course: string) =>
  props.slots.find(
    (s) => s.dayofweek === day && s.lunch === moment && s.type === course,
  );

const pickFor = (slot: MealSlot | undefined): RecipePick =>
  slot
    ? { id: slot.recipeId, title: slot.recipeTitle, image: slot.recipeImage }
    : { id: null, title: "", image: null };

const onUpdate = (slot: MealSlot | undefined, pick: RecipePick) => {
  if (!slot) return;
  emit("update-slot", slot.key, pick);
};

// The grid defaults to a roomier layout so the recipe dropdowns (and the
// full recipe name inside them) are easy to read; "Réduire" switches back
// to the compact columns for a quick overview.
const expanded = ref(true);
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex justify-end">
      <button
        type="button"
        class="text-[12px] font-semibold text-sup-dark-green hover:underline"
        @click="expanded = !expanded"
      >
        {{ expanded ? "Réduire le tableau" : "Agrandir le tableau" }}
      </button>
    </div>

    <div v-for="moment in MEAL_MOMENTS" :key="moment.value">
      <p class="mb-2 text-[13px] font-bold text-sup-dark-green">
        {{ moment.label }}
      </p>
      <div class="overflow-x-auto rounded-md border border-sup-border">
        <table class="w-full border-collapse text-left text-[12.5px]">
          <thead>
            <tr class="bg-sup-light-gray">
              <th class="w-20 px-3 py-2 font-semibold text-gray-400"></th>
              <th
                v-for="day in days"
                :key="day.value"
                class="px-2 py-2 font-semibold text-sup-very-gray transition-[min-width]"
                :class="expanded ? 'min-w-[260px]' : 'min-w-[150px]'"
              >
                {{ day.label }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="course in MEAL_COURSES"
              :key="course.value"
              class="border-t border-sup-border"
            >
              <td class="px-3 py-2 align-top font-semibold text-gray-400">
                {{ course.label }}
              </td>
              <td
                v-for="day in days"
                :key="day.value"
                class="px-2 py-2 align-top"
                :class="expanded ? 'py-3' : 'py-2'"
              >
                <RecipePicker
                  :model-value="
                    pickFor(slotFor(day.value, moment.value, course.value))
                  "
                  :expanded="expanded"
                  @update:model-value="
                    (v) =>
                      onUpdate(
                        slotFor(day.value, moment.value, course.value),
                        v,
                      )
                  "
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
