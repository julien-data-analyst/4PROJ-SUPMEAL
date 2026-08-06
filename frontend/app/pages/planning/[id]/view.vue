<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import IconChevronLeft from "~/components/icons/IconChevronLeft.vue";
import IconTrash from "~/components/icons/IconTrash.vue";
import IconAlertTriangle from "~/components/icons/IconAlertTriangle.vue";
import IconCalendar from "~/components/icons/IconCalendar.vue";
import PlanningMealsGrid from "~/components/planning/PlanningMealsGrid.vue";
import DeletePlanningModal from "~/components/planning/DeletePlanningModal.vue";
import DiscussionPanel from "~/components/cookbook/DiscussionPanel.vue";
import { usePlanningView } from "~/composables/usePlanningEditView";
import { PLANNING_TYPE_LABELS } from "~/composables/usePlanning";
import { useGoBack } from "~/composables/useGoBack";

definePageMeta({ layout: "app" });

const planningId = Number(useRoute().params.id);
const goBack = useGoBack("/planning");

const {
  isLoading,
  deleteModalOpen,
  planning,
  canEdit,
  canManage,
  cookbookName,
  confirmDelete,
} = usePlanningView(planningId);
</script>

<template>
  <div class="mx-auto max-w-[980px]">
    <div class="mb-[22px] flex flex-wrap items-center justify-between gap-4">
      <button
        type="button"
        class="flex items-center gap-[6px] text-[13px] font-medium text-gray-400 hover:text-sup-dark-green"
        @click="goBack"
      >
        <IconChevronLeft size="xs" />
        Retour
      </button>

      <div v-if="planning" class="flex flex-wrap items-center gap-[10px]">
        <button
          v-if="canManage"
          type="button"
          class="inline-flex h-[34px] w-[34px] items-center justify-center rounded-md border border-red-200 text-sup-red-error transition hover:bg-sup-red-error/10"
          title="Supprimer le planning"
          @click="deleteModalOpen = true"
        >
          <IconTrash size="xs" />
        </button>
        <AppButton
          v-if="canEdit"
          variant="primary"
          :to="`/planning/${planningId}/edit`"
        >
          Modifier
        </AppButton>
      </div>
    </div>

    <div v-if="isLoading" class="py-16 text-center text-[13px] text-gray-400">
      Chargement du planning...
    </div>

    <template v-else-if="planning">
      <div class="mb-4 flex items-start gap-4">
        <div
          class="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-md bg-sup-light-gray"
        >
          <img
            v-if="planning.icon"
            :src="planning.icon"
            :alt="planning.name"
            class="h-10 w-10 object-contain"
          />
          <IconCalendar v-else size="md" />
        </div>

        <div class="flex-1">
          <h1 class="mb-[6px] text-[24px] font-semibold text-sup-very-gray">
            {{ planning.name }}
          </h1>
          <div
            class="flex flex-wrap items-center gap-2 text-[12.5px] text-gray-400"
          >
            <span
              class="inline-flex items-center rounded-full border border-sup-border bg-sup-withe px-[10px] py-[3px] text-[11px] font-semibold text-gray-400"
            >
              {{ PLANNING_TYPE_LABELS[planning.type] }}
            </span>
            <NuxtLink
              v-if="planning.cookbook"
              :to="`/cookbooks/${planning.cookbook}/view`"
              class="inline-flex items-center rounded-full border border-sup-border bg-sup-withe px-[10px] py-[3px] text-[11px] font-semibold text-gray-400 hover:text-sup-dark-green hover:underline"
            >
              Dans le cookbook « {{ cookbookName || "…" }} »
            </NuxtLink>
            <span
              v-else
              class="inline-flex items-center rounded-full border border-sup-border bg-sup-withe px-[10px] py-[3px] text-[11px] font-semibold text-gray-400"
            >
              Personnel
            </span>
            <span
              >par
              {{
                planning.creator.first_name || planning.creator.username
              }}</span
            >
            <span
              >· {{ planning.meals.length }} repas planifié{{
                planning.meals.length > 1 ? "s" : ""
              }}</span
            >
          </div>
        </div>
      </div>

      <div class="rounded-[10px] border border-sup-border bg-sup-withe p-6">
        <PlanningMealsGrid :type="planning.type" :meals="planning.meals" />
      </div>

      <div
        v-if="!canEdit"
        class="mt-4 flex items-center gap-2 rounded-md border border-[#F0DE9A] bg-sup-yellow-warning/15 px-[14px] py-[10px] text-[12.5px] font-medium text-[#8A6D00]"
      >
        <IconAlertTriangle size="xs" class="shrink-0" />
        Vous n'avez pas la permission de modifier ce planning.
      </div>

      <DiscussionPanel
        v-if="planning.cookbook"
        class="mt-4"
        :cookbook-id="planning.cookbook"
        title="Discussion du cookbook"
      />
    </template>

    <DeletePlanningModal
      v-if="planning"
      :open="deleteModalOpen"
      :planning-name="planning.name"
      @close="deleteModalOpen = false"
      @confirm="confirmDelete"
    />
  </div>
</template>
