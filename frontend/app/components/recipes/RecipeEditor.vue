<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import IconChevronLeft from "~/components/icons/IconChevronLeft.vue";
import IconEye from "~/components/icons/IconEye.vue";
import IconTrash from "~/components/icons/IconTrash.vue";
import IconSave from "~/components/icons/IconSave.vue";
import IconCamera from "~/components/icons/IconCamera.vue";
import IconPlus from "~/components/icons/IconPlus.vue";
import StepEditor from "~/components/recipes/StepEditor.vue";
import IngredientsPanel from "~/components/recipes/IngredientsPanel.vue";
import TagsPanel from "~/components/recipes/TagsPanel.vue";
import DiscussionPanel from "~/components/recipes/DiscussionPanel.vue";
import DeleteRecipeModal from "~/components/recipes/DeleteRecipeModal.vue";
import { useRecipeStore } from "~/stores/useRecipeStore";
import type { RecipeWritePayload } from "~/stores/useRecipeStore";
import {
  emptyStepLine,
  fileToDataUrl,
  minutesToDury,
  recipeToIngredientLines,
  recipeToStepLines,
  recipeToTagLines,
  relativeTime,
  formatCookingDuration,
} from "~/composables/useRecipes";
import type { IngredientLine, StepLine, TagLine } from "~/composables/useRecipes";

const props = defineProps<{
  mode: "create" | "edit";
  recipeId?: number;
}>();

const store = useRecipeStore();

const title = ref("");
const source = ref("");
const cookingDuration = ref("");
const image = ref<string | null>(null);

const ingredientLines = ref<IngredientLine[]>([]);
const tagLines = ref<TagLine[]>([]);
const stepLines = ref<StepLine[]>([emptyStepLine()]);

const previewMode = ref(false);
const isLoading = ref(props.mode === "edit");
const isSaving = ref(false);
const saveError = ref("");
const savedNotice = ref(false);
const deleteModalOpen = ref(false);
const isDeleting = ref(false);

const currentRecipe = computed(() => store.currentRecipe);

const loadRecipe = async () => {
  if (props.mode !== "edit" || !props.recipeId) return;
  isLoading.value = true;
  try {
    const recipe = await store.fetchRecipe(props.recipeId);
    title.value = recipe.title;
    source.value = recipe.source ?? "";
    cookingDuration.value = recipe.cooking_duration ?? "";
    image.value = recipe.image;
    ingredientLines.value = recipeToIngredientLines(recipe);
    tagLines.value = recipeToTagLines(recipe);
    stepLines.value = recipeToStepLines(recipe).length
      ? recipeToStepLines(recipe)
      : [emptyStepLine()];
  } finally {
    isLoading.value = false;
  }
};

onMounted(loadRecipe);

const onImageChange = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  image.value = await fileToDataUrl(file);
};

const addStep = () => {
  stepLines.value = [...stepLines.value, emptyStepLine()];
};

const removeStep = (index: number) => {
  stepLines.value = stepLines.value.filter((_, i) => i !== index);
  if (!stepLines.value.length) stepLines.value = [emptyStepLine()];
};

const moveStep = (index: number, direction: -1 | 1) => {
  const target = index + direction;
  if (target < 0 || target >= stepLines.value.length) return;
  const next = [...stepLines.value];
  const [moved] = next.splice(index, 1);
  if (!moved) return;
  next.splice(target, 0, moved);
  stepLines.value = next;
};

const validate = (): string | null => {
  if (!title.value.trim()) return "Le titre de la recette est obligatoire.";

  const usedIngredientNames = new Set<string>();
  for (const line of ingredientLines.value) {
    if (!line.name.trim()) continue;
    if (!line.ingredientId && !line.image) {
      return `L'ingrédient « ${line.name} » est nouveau : une image est obligatoire.`;
    }
    if (!line.quantity || Number(line.quantity) <= 0) {
      return `Indiquez une quantité pour « ${line.name} ».`;
    }
    if (!line.personNumbers || Number(line.personNumbers) < 1) {
      return `Indiquez un nombre de personnes pour « ${line.name} ».`;
    }
    const key = line.name.trim().toLowerCase();
    if (usedIngredientNames.has(key)) {
      return `L'ingrédient « ${line.name} » est ajouté plusieurs fois.`;
    }
    usedIngredientNames.add(key);
  }

  const usedTagNames = new Set<string>();
  for (const tag of tagLines.value) {
    if (!tag.name.trim()) continue;
    const key = tag.name.trim().toLowerCase();
    if (usedTagNames.has(key)) {
      return `Le tag « ${tag.name} » est ajouté plusieurs fois.`;
    }
    usedTagNames.add(key);
  }

  return null;
};

const buildPayload = (): RecipeWritePayload => ({
  title: title.value.trim(),
  image: image.value || null,
  source: source.value.trim() || null,
  cooking_duration: cookingDuration.value ? Number(cookingDuration.value) : null,
  ingredients: ingredientLines.value
    .filter((l) => l.name.trim())
    .map((l) => ({
      name: l.name.trim(),
      image: l.image || null,
      quantity: Number(l.quantity) || 0,
      unity: l.unity.trim() || null,
      person_numbers: Number(l.personNumbers) || 1,
    })),
  tags: tagLines.value
    .filter((t) => t.name.trim())
    .map((t) => ({
      name: t.name.trim(),
      type: t.type,
      description: t.description.trim() || null,
    })),
  steps: stepLines.value
    .filter((s) => s.description.trim())
    .map((s, i) => ({
      description: s.description,
      step_number: i + 1,
      dury: minutesToDury(s.durationMinutes),
      type: s.type,
    })),
});

const save = async () => {
  saveError.value = "";
  savedNotice.value = false;
  const error = validate();
  if (error) {
    saveError.value = error;
    return;
  }

  isSaving.value = true;
  try {
    const payload = buildPayload();
    if (props.mode === "create") {
      const recipe = await store.createRecipe(payload);
      await navigateTo(`/recipes/${recipe.id}/edit`);
    } else if (props.recipeId) {
      await store.updateRecipe(props.recipeId, payload);
      savedNotice.value = true;
      setTimeout(() => (savedNotice.value = false), 2500);
    }
  } catch {
    saveError.value = "Impossible d'enregistrer la recette. Vérifiez les champs et réessayez.";
  } finally {
    isSaving.value = false;
  }
};

const confirmDelete = async () => {
  if (!props.recipeId || isDeleting.value) return;
  isDeleting.value = true;
  try {
    await store.deleteRecipe(props.recipeId);
    deleteModalOpen.value = false;
    await navigateTo("/recipes");
  } catch {
    saveError.value = "Impossible de supprimer la recette.";
    deleteModalOpen.value = false;
  } finally {
    isDeleting.value = false;
  }
};
</script>

<template>
  <div class="mx-auto max-w-[980px]">
    <div class="mb-[22px] flex flex-wrap items-center justify-between gap-4">
      <NuxtLink
        to="/recipes"
        class="flex items-center gap-[6px] text-[13px] font-medium text-gray-400 hover:text-sup-dark-green"
      >
        <IconChevronLeft size="xs" />
        Retour
      </NuxtLink>

      <div class="flex flex-wrap items-center gap-[10px]">
        <AppButton type="button" variant="secondary" @click="previewMode = !previewMode">
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
        <label class="group relative flex h-16 w-16 shrink-0 cursor-pointer items-center justify-center overflow-hidden rounded-md border border-dashed border-sup-border bg-sup-light-gray text-gray-400">
          <img v-if="image" :src="image" alt="" class="h-full w-full object-cover" />
          <IconCamera v-else size="sm" />
          <input type="file" accept="image/*" class="hidden" @change="onImageChange" />
        </label>

        <div class="flex-1">
          <input
            v-model="title"
            type="text"
            placeholder="Titre de la recette"
            class="mb-1 w-full border-none bg-transparent text-[22px] font-bold text-sup-very-gray outline-none"
          />
          <div class="flex flex-wrap items-center gap-2">
            <span
              class="inline-flex items-center gap-1 rounded-full bg-sup-light-green/15 px-[10px] py-[3px] text-[11px] font-semibold text-sup-dark-green"
            >
              {{ currentRecipe?.cookbook ? "Dans un cookbook" : "Personnel" }}
            </span>
            <span v-if="currentRecipe" class="text-[12.5px] text-gray-400">
              Dernière modification : {{ relativeTime(currentRecipe.updated_at) }}
            </span>
            <span v-if="savedNotice" class="text-[12.5px] font-semibold text-sup-dark-green">
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
          <span v-if="cookingDuration" class="shrink-0 text-[12.5px] text-gray-400">
            {{ formatCookingDuration(cookingDuration) }}
          </span>
        </div>
      </div>

      <p v-if="saveError" class="mb-4 rounded-md bg-sup-red-error/10 px-4 py-3 text-[13px] text-sup-red-error">
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
            @update:model-value="(v) => (stepLines = stepLines.map((s, i) => (i === index ? v : s)))"
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
          />
        </div>
      </div>
    </template>

    <DeleteRecipeModal
      :open="deleteModalOpen"
      :recipe-title="title"
      @close="deleteModalOpen = false"
      @confirm="confirmDelete"
    />
  </div>
</template>
