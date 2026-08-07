<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import IconUpload from "~/components/icons/IconUpload.vue";
import IconClose from "~/components/icons/IconClose.vue";
import { isJsonFile } from "~/composables/useImportExport";
import { useToastStore } from "~/stores/useToastStore";

const props = withDefaults(
  defineProps<{
    label: string;
    busy?: boolean;
  }>(),
  { busy: false },
);

const emit = defineEmits<{ import: [file: File] }>();

const toast = useToastStore();
const dropZoneRef = ref<HTMLElement | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);

const acceptFile = (file: File | null | undefined) => {
  if (!file) return;
  if (!isJsonFile(file)) {
    toast.error("Seuls les fichiers .json sont acceptés.");
    return;
  }
  selectedFile.value = file;
};

const onDrop = (files: File[] | null) => acceptFile(files?.[0]);

const { isOverDropZone } = useDropZone(dropZoneRef, { onDrop });

const onBrowseChange = (event: Event) => {
  const input = event.target as HTMLInputElement;
  acceptFile(input.files?.[0]);
  input.value = "";
};

const clearFile = () => {
  selectedFile.value = null;
};

const doImport = () => {
  if (!selectedFile.value || props.busy) return;
  emit("import", selectedFile.value);
};

defineExpose({ clearFile });
</script>

<template>
  <div>
    <div
      ref="dropZoneRef"
      class="flex flex-col items-center justify-center gap-2 rounded-[10px] border-2 border-dashed p-8 text-center transition"
      :class="
        isOverDropZone
          ? 'border-sup-dark-green bg-sup-light-green/10'
          : 'border-sup-border bg-sup-withe'
      "
    >
      <IconUpload size="lg" class="text-gray-400" />
      <p class="text-[13px] text-sup-very-gray">
        Glissez-déposez un fichier <strong>.json</strong> ici, ou
        <button
          type="button"
          class="font-semibold text-sup-dark-green hover:underline"
          @click="fileInputRef?.click()"
        >
          parcourez vos fichiers
        </button>
      </p>
      <input
        ref="fileInputRef"
        type="file"
        accept=".json,application/json"
        class="hidden"
        @change="onBrowseChange"
      />
      <p
        v-if="selectedFile"
        class="mt-1 flex items-center gap-2 text-[12.5px] text-sup-very-gray"
      >
        {{ selectedFile.name }}
        <button
          type="button"
          class="text-gray-400 hover:text-sup-red-error"
          title="Retirer"
          @click.stop="clearFile"
        >
          <IconClose size="xs" />
        </button>
      </p>
    </div>

    <AppButton
      class="mt-3"
      variant="primary"
      :disabled="!selectedFile || busy"
      @click="doImport"
    >
      {{ busy ? "Import en cours..." : label }}
    </AppButton>
  </div>
</template>
