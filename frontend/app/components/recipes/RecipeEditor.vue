<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import IconChevronLeft from "~/components/icons/IconChevronLeft.vue";
import IconEye from "~/components/icons/IconEye.vue";
import IconTrash from "~/components/icons/IconTrash.vue";
import IconSave from "~/components/icons/IconSave.vue";
import IconCamera from "~/components/icons/IconCamera.vue";
import IconPlus from "~/components/icons/IconPlus.vue";
import IconClock from "~/components/icons/IconClock.vue";
import StepEditor from "~/components/recipes/StepEditor.vue";
import IngredientsPanel from "~/components/recipes/IngredientsPanel.vue";
import TagsPanel from "~/components/recipes/TagsPanel.vue";
import DiscussionPanel from "~/components/cookbook/DiscussionPanel.vue";
import DeleteRecipeModal from "~/components/recipes/DeleteRecipeModal.vue";
import { useRecipeEditForm } from "~/composables/useRecipesEditView";
import { useGoBack } from "~/composables/useGoBack";

const props = defineProps<{
  mode: "create" | "edit";
  recipeId?: number;
}>();

const goBack = useGoBack("/recipes");

const {
  title,
  source,
  cookingDuration,
  image,
  ingredientLines,
  tagLines,
  stepLines,
  previewMode,
  isLoading,
  isSaving,
  saveError,
  savedNotice,
  deleteModalOpen,
  currentRecipe,
  cookbookId,
  cookbookName,
  totalMinutes,
  onImageChange,
  addStep,
  removeStep,
  moveStep,
  save,
  confirmDelete,
  relativeTime,
  formatCookingDuration,
} = useRecipeEditForm(props);
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

      <div class="flex flex-wrap items-center gap-[10px]">
        <AppButton
          type="button"
          variant="secondary"
          @click="previewMode = !previewMode"
        >
          <template #icon><IconEye size="xs" /></template>
          {{ previewMode ? "Édition" : "Aperçu" }}
        </AppButton>
        <button
          v-if="mode === 'edit'"
          type="button"
          class="inline-flex h-[34px] w-[34px] items-center justify-center rounded-md border border-red-200 text-sup-red-error transition hover:bg-sup-red-error/10"
          title="Supprimer la recette"
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
      Chargement de la recette...
    </div>

    <template v-else>
      <div class="mb-4 flex items-start gap-4">
        <label
          class="group relative flex h-16 w-16 shrink-0 cursor-pointer items-center justify-center overflow-hidden rounded-md border border-dashed border-sup-border bg-sup-light-gray text-gray-400"
        >
          <img
            v-if="image"
            :src="image"
            alt=""
            class="h-full w-full object-cover"
          />
          <IconCamera v-else size="sm" />
          <input
            type="file"
            accept="image/png,image/jpeg,image/svg+xml"
            class="hidden"
            @change="onImageChange"
          />
        </label>

        <div class="flex-1">
          <input
            v-model="title"
            type="text"
            placeholder="Titre de la recette"
            class="mb-1 w-full border-none bg-transparent text-[22px] font-bold text-sup-very-gray outline-none"
          />
          <div class="flex flex-wrap items-center gap-2">
            <NuxtLink
              v-if="cookbookId"
              :to="`/cookbooks/${cookbookId}/view`"
              class="inline-flex items-center gap-1 rounded-full bg-sup-light-green/15 px-[10px] py-[3px] text-[11px] font-semibold text-sup-dark-green hover:underline"
            >
              Dans le cookbook « {{ cookbookName || "…" }} »
            </NuxtLink>
            <span
              v-else
              class="inline-flex items-center gap-1 rounded-full bg-sup-light-green/15 px-[10px] py-[3px] text-[11px] font-semibold text-sup-dark-green"
            >
              Personnel
            </span>
            <span v-if="currentRecipe" class="text-[12.5px] text-gray-400">
              Dernière modification :
              {{ relativeTime(currentRecipe.updated_at) }}
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

      <div class="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <input
          v-model="source"
          type="text"
          placeholder="Source (optionnel)"
          class="w-full rounded-md border border-sup-border bg-sup-withe px-3 py-[9px] text-[13.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30"
        />
        <div class="flex items-center gap-2">
          <input
            v-model="cookingDuration"
            type="number"
            min="0"
            placeholder="Durée de cuisson (minutes)"
            class="w-full rounded-md border border-sup-border bg-sup-withe px-3 py-[9px] text-[13.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30"
          />
          <span
            v-if="cookingDuration"
            class="shrink-0 text-[12.5px] text-gray-400"
          >
            {{ formatCookingDuration(cookingDuration) }}
          </span>
        </div>
      </div>

      <div
        v-if="totalMinutes > 0"
        class="mb-4 flex items-center gap-2 rounded-md border border-sup-border bg-sup-light-green/10 px-4 py-[10px] text-[13px] font-semibold text-sup-dark-green"
      >
        <IconClock size="xs" />
        Temps de préparation estimé : {{ formatCookingDuration(totalMinutes) }}
      </div>

      <p
        v-if="saveError"
        class="mb-4 rounded-md bg-sup-red-error/10 px-4 py-3 text-[13px] text-sup-red-error"
      >
        {{ saveError }}
      </p>

      <div class="grid grid-cols-1 gap-5 lg:grid-cols-[320px_1fr_260px]">
        <div class="order-2 lg:order-1">
          <IngredientsPanel v-model="ingredientLines" />
        </div>

        <div class="order-1 flex flex-col gap-3 lg:order-2">
          <p class="text-[17px] font-bold text-sup-dark-green">Étapes</p>
          <StepEditor
            v-for="(step, index) in stepLines"
            :key="step.key"
            :model-value="step"
            :index="index"
            :total="stepLines.length"
            :preview-mode="previewMode"
            @update:model-value="
              (v) =>
                (stepLines = stepLines.map((s, i) => (i === index ? v : s)))
            "
            @remove="removeStep(index)"
            @move-up="moveStep(index, -1)"
            @move-down="moveStep(index, 1)"
          />
          <button
            type="button"
            class="flex items-center justify-center gap-2 rounded-md border border-dashed border-sup-border py-[9px] text-[13px] font-medium text-sup-dark-green hover:bg-sup-light-green/10"
            @click="addStep"
          >
            <IconPlus size="xs" />
            Ajouter une étape
          </button>
        </div>

        <div class="order-3 flex flex-col gap-5">
          <TagsPanel v-model="tagLines" />
          <DiscussionPanel
            v-if="currentRecipe?.cookbook"
            :cookbook-id="currentRecipe.cookbook"
            :recipe-id="currentRecipe.id"
            title="Discussion sur cette recette"
          />
        </div>
      </div>
    </template>

    <DeleteRecipeModal
      :open="deleteModalOpen"
      :recipe-title="title"
      :used-in-plannings="currentRecipe?.used_in_plannings"
      @close="deleteModalOpen = false"
      @confirm="confirmDelete"
    />
  </div>
</template>
