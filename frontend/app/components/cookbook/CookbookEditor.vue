<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import IconChevronLeft from "~/components/icons/IconChevronLeft.vue";
import IconTrash from "~/components/icons/IconTrash.vue";
import IconSave from "~/components/icons/IconSave.vue";
import IconCamera from "~/components/icons/IconCamera.vue";
import DeleteCookbookModal from "~/components/cookbook/DeleteCookbookModal.vue";
import { useCookbookEditForm } from "~/composables/useCookbooksEditView";
import { useGoBack } from "~/composables/useGoBack";

const props = defineProps<{
  mode: "create" | "edit";
  cookbookId?: number;
}>();

const goBack = useGoBack(
  props.mode === "edit" && props.cookbookId
    ? `/cookbooks/${props.cookbookId}/view`
    : "/cookbooks",
);

const {
  name,
  icon,
  isLoading,
  isSaving,
  saveError,
  savedNotice,
  deleteModalOpen,
  currentCookbook,
  onIconChange,
  save,
  confirmDelete,
} = useCookbookEditForm(props);
</script>

<template>
  <div class="mx-auto max-w-[640px]">
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
        <button
          v-if="mode === 'edit'"
          type="button"
          class="inline-flex h-[34px] w-[34px] items-center justify-center rounded-md border border-red-200 text-sup-red-error transition hover:bg-sup-red-error/10"
          title="Supprimer le cookbook"
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
      Chargement du cookbook...
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
            placeholder="Nom du cookbook"
            class="mb-1 w-full border-none bg-transparent text-[22px] font-bold text-sup-very-gray outline-none"
          />
          <div class="flex flex-wrap items-center gap-2">
            <span v-if="currentCookbook" class="text-[12.5px] text-gray-400">
              {{ currentCookbook.recipes.length }} recette{{
                currentCookbook.recipes.length > 1 ? "s" : ""
              }}
              · {{ currentCookbook.plannings.length }} planning{{
                currentCookbook.plannings.length > 1 ? "s" : ""
              }}
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
    </template>

    <DeleteCookbookModal
      v-if="mode === 'edit'"
      :open="deleteModalOpen"
      :cookbook-name="name"
      :recipe-count="currentCookbook?.recipes.length"
      :planning-count="currentCookbook?.plannings.length"
      @close="deleteModalOpen = false"
      @confirm="confirmDelete"
    />
  </div>
</template>
