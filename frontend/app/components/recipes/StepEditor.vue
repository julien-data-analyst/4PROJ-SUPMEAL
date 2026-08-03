<script setup lang="ts">
import type { StepLine } from "~/composables/useRecipes";
import {
  applyMarkdownAction,
  renderStepMarkdown,
} from "~/composables/useRecipes";
import IconBold from "~/components/icons/IconBold.vue";
import IconItalic from "~/components/icons/IconItalic.vue";
import IconListBullet from "~/components/icons/IconListBullet.vue";
import IconChevron from "~/components/icons/IconChevron.vue";
import IconTrash from "~/components/icons/IconTrash.vue";

const props = defineProps<{
  index: number;
  total: number;
  previewMode: boolean;
}>();

const emit = defineEmits<{
  remove: [];
  "move-up": [];
  "move-down": [];
}>();

const step = defineModel<StepLine>({ required: true });

const textareaRef = ref<HTMLTextAreaElement | null>(null);

const format = (action: "bold" | "italic" | "list") => {
  if (!textareaRef.value) return;
  step.value.description = applyMarkdownAction(textareaRef.value, action);
  nextTick(() => textareaRef.value?.focus());
};

const preview = computed(() => renderStepMarkdown(step.value.description));
</script>

<template>
  <div
    class="rounded-[14px] border border-sup-border bg-sup-withe p-[18px] shadow-sm"
  >
    <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
      <p class="text-[14.5px] font-bold text-sup-very-gray">
        Étape {{ props.index + 1 }}
      </p>
      <div class="flex items-center gap-2">
        <select
          v-model="step.type"
          class="rounded-md border border-sup-border bg-sup-withe px-2 py-1.5 text-[12px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none"
        >
          <option value="prep">Préparation</option>
          <option value="cook">Cuisson</option>
        </select>
        <input
          v-model="step.durationMinutes"
          type="number"
          min="0"
          placeholder="min"
          class="w-20 rounded-md border border-sup-border bg-sup-withe px-2 py-1.5 text-[12px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none"
        />
        <button
          type="button"
          class="rounded-md border border-sup-border p-1.5 text-sup-very-gray hover:bg-sup-light-gray disabled:opacity-30"
          :disabled="props.index === 0"
          title="Monter"
          @click="emit('move-up')"
        >
          <IconChevron size="xs" direction="up" />
        </button>
        <button
          type="button"
          class="rounded-md border border-sup-border p-1.5 text-sup-very-gray hover:bg-sup-light-gray disabled:opacity-30"
          :disabled="props.index === props.total - 1"
          title="Descendre"
          @click="emit('move-down')"
        >
          <IconChevron size="xs" direction="down" />
        </button>
        <button
          type="button"
          class="rounded-md border border-sup-border p-1.5 text-sup-red-error hover:bg-sup-red-error/10"
          title="Supprimer l'étape"
          @click="emit('remove')"
        >
          <IconTrash size="xs" />
        </button>
      </div>
    </div>

    <template v-if="!props.previewMode">
      <div
        class="mb-2 flex items-center gap-1 rounded-md border border-sup-border bg-sup-light-gray p-1"
      >
        <button
          type="button"
          class="rounded p-1.5 text-sup-very-gray hover:bg-sup-withe"
          title="Gras"
          @click="format('bold')"
        >
          <IconBold size="xs" />
        </button>
        <button
          type="button"
          class="rounded p-1.5 text-sup-very-gray hover:bg-sup-withe"
          title="Italique"
          @click="format('italic')"
        >
          <IconItalic size="xs" />
        </button>
        <button
          type="button"
          class="rounded p-1.5 text-sup-very-gray hover:bg-sup-withe"
          title="Liste"
          @click="format('list')"
        >
          <IconListBullet size="xs" />
        </button>
      </div>
      <textarea
        ref="textareaRef"
        v-model="step.description"
        rows="4"
        placeholder="Décrivez cette étape... (**gras**, *italique*, - liste)"
        class="w-full resize-y rounded-md border border-sup-border bg-sup-withe p-3 text-[13.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30"
      />
    </template>
    <div
      v-else
      class="rounded-md border border-sup-border bg-sup-light-gray p-3 text-[13.5px] text-sup-very-gray"
      v-html="preview || '<p class=\'text-gray-400\'>Aucune description.</p>'"
    />
  </div>
</template>
