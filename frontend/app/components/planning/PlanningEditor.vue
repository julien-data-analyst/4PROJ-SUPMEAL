<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import IconChevronLeft from "~/components/icons/IconChevronLeft.vue";
import IconTrash from "~/components/icons/IconTrash.vue";
import IconSave from "~/components/icons/IconSave.vue";
import IconCamera from "~/components/icons/IconCamera.vue";
import MealPlanEditor from "~/components/planning/MealPlanEditor.vue";
import DeletePlanningModal from "~/components/planning/DeletePlanningModal.vue";
import { usePlanningEditForm } from "~/composables/usePlanningEditView";
import { PLANNING_TYPE_LABELS } from "~/composables/usePlanning";
import { relativeTime } from "~/composables/useRecipes";

const props = defineProps<{
  mode: "create" | "edit";
  planningId?: number;
}>();

const {
  name,
  icon,
  type,
  slots,
  isLoading,
  isSaving,
  saveError,
  savedNotice,
  deleteModalOpen,
  currentPlanning,
  scheduledCount,
  onTypeChange,
  onIconChange,
  setSlotRecipe,
  save,
  confirmDelete,
} = usePlanningEditForm(props);
</script>

<template>
  <div class="mx-auto max-w-[980px]">
    <div class="mb-[22px] flex flex-wrap items-center justify-between gap-4">
      <NuxtLink
        to="/planning"
        class="flex items-center gap-[6px] text-[13px] font-medium text-gray-400 hover:text-sup-dark-green"
      >
        <IconChevronLeft size="xs" />
        Retour
      </NuxtLink>

      <div class="flex flex-wrap items-center gap-[10px]">
        <button
          v-if="mode === 'edit'"
          type="button"
          class="inline-flex h-[34px] w-[34px] items-center justify-center rounded-md border border-red-200 text-sup-red-error transition hover:bg-sup-red-error/10"
          title="Supprimer le planning"
          @click="deleteModalOpen = true"
        >
          <IconTrash size="xs" />
        </button>
        <AppButton variant="primary" :disabled="isSaving" @click="save">
          <template #icon><IconSave size="xs" /></template>
          {{ isSaving ? "Enregistrement..." : "Enregistrer" }}
        </AppButton>
      </div>
    </div>

    <div v-if="isLoading" class="py-16 text-center text-[13px] text-gray-400">
      Chargement du planning...
    </div>

    <template v-else>
      <div class="mb-4 flex items-start gap-4">
        <label
          class="group relative flex h-16 w-16 shrink-0 cursor-pointer items-center justify-center overflow-hidden rounded-md border border-dashed border-sup-border bg-sup-light-gray text-gray-400"
        >
          <img
            v-if="icon"
            :src="icon"
            alt=""
            class="h-full w-full object-cover"
          />
          <IconCamera v-else size="sm" />
          <input
            type="file"
            accept="image/png,image/jpeg,image/svg+xml"
            class="hidden"
            @change="onIconChange"
          />
        </label>

        <div class="flex-1">
          <input
            v-model="name"
            type="text"
            placeholder="Nom du planning"
            class="mb-1 w-full border-none bg-transparent text-[22px] font-bold text-sup-very-gray outline-none"
          />
          <div class="flex flex-wrap items-center gap-2">
            <select
              v-if="mode === 'create'"
              :value="type"
              class="rounded-full border border-sup-border bg-sup-withe px-[10px] py-[3px] text-[11px] font-semibold text-sup-dark-green focus:border-sup-dark-green focus:outline-none"
              @change="onTypeChange"
            >
              <option value="hebdomadaire">Hebdomadaire (7 jours)</option>
              <option value="journalier">Journalier (1 jour)</option>
            </select>
            <span
              v-else
              class="inline-flex items-center gap-1 rounded-full bg-sup-light-green/15 px-[10px] py-[3px] text-[11px] font-semibold text-sup-dark-green"
            >
              {{ PLANNING_TYPE_LABELS[type] }}
            </span>
            <span class="text-[12.5px] text-gray-400">
              {{ scheduledCount }} repas planifié{{
                scheduledCount > 1 ? "s" : ""
              }}
            </span>
            <span v-if="currentPlanning" class="text-[12.5px] text-gray-400">
              · Dernière modification :
              {{ relativeTime(currentPlanning.updated_at) }}
            </span>
            <span
              v-if="savedNotice"
              class="text-[12.5px] font-semibold text-sup-dark-green"
            >
              Enregistré ✓
            </span>
          </div>
        </div>
      </div>

      <p
        v-if="saveError"
        class="mb-4 rounded-md bg-sup-red-error/10 px-4 py-3 text-[13px] text-sup-red-error"
      >
        {{ saveError }}
      </p>

      <div
        class="rounded-[14px] border border-sup-border bg-sup-withe p-[18px] shadow-sm"
      >
        <MealPlanEditor
          :type="type"
          :slots="slots"
          @update-slot="setSlotRecipe"
        />
      </div>
    </template>

    <DeletePlanningModal
      :open="deleteModalOpen"
      :planning-name="name"
      @close="deleteModalOpen = false"
      @confirm="confirmDelete"
    />
  </div>
</template>
