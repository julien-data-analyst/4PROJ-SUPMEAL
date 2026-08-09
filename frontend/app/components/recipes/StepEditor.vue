<script setup lang="ts">
import { useEditor, EditorContent } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import { Markdown } from "tiptap-markdown";
import type { StepLine } from "~/composables/useRecipes";
import IconBold from "~/components/icons/IconBold.vue";
import IconItalic from "~/components/icons/IconItalic.vue";
import IconListBullet from "~/components/icons/IconListBullet.vue";
import IconChevron from "~/components/icons/IconChevron.vue";
import IconTrash from "~/components/icons/IconTrash.vue";

const props = defineProps<{
  index: number;
  total: number;
}>();

const emit = defineEmits<{
  remove: [];
  "move-up": [];
  "move-down": [];
}>();

const step = defineModel<StepLine>({ required: true });

// WYSIWYG editor: the user only ever sees the rendered result (bold text
// looks bold, "- " turns into a real bullet, etc.) - the markdown syntax
// itself is never shown. `step.description` still stores plain markdown
// (via the Markdown extension's serializer) so the API contract and the
// read-only rendering in recipe view.vue (renderStepMarkdown) don't change.
// Only the subset of nodes renderStepMarkdown knows how to render is kept
// enabled (bold, italic, headings 1-3, bullet/ordered lists, paragraphs,
// hard breaks) - link/strike/code/blockquote/etc. are disabled so the
// editor can't produce markdown the read-only view wouldn't understand.
const editor = useEditor({
  content: step.value.description,
  extensions: [
    StarterKit.configure({
      heading: { levels: [1, 2, 3] },
      link: false,
      underline: false,
      strike: false,
      code: false,
      codeBlock: false,
      blockquote: false,
      horizontalRule: false,
    }),
    Placeholder.configure({
      placeholder: "Décrivez cette étape... (gras, italique, liste)",
    }),
    Markdown.configure({
      html: false,
      linkify: false,
      breaks: false,
      tightLists: true,
    }),
  ],
  editorProps: {
    attributes: {
      class: "tiptap-content",
    },
  },
  onUpdate: ({ editor: e }) => {
    step.value.description = e.storage.markdown.getMarkdown();
  },
});

const format = (action: "bold" | "italic" | "list") => {
  const chain = editor.value?.chain().focus();
  if (!chain) return;
  if (action === "bold") chain.toggleBold().run();
  else if (action === "italic") chain.toggleItalic().run();
  else chain.toggleBulletList().run();
};

const isActive = (action: "bold" | "italic" | "list"): boolean => {
  if (!editor.value) return false;
  if (action === "list") return editor.value.isActive("bulletList");
  return editor.value.isActive(action);
};
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

    <div
      class="mb-2 flex items-center gap-1 rounded-md border border-sup-border bg-sup-light-gray p-1"
    >
      <button
        type="button"
        class="rounded p-1.5 text-sup-very-gray hover:bg-sup-withe"
        :class="{ 'bg-sup-withe text-sup-dark-green': isActive('bold') }"
        title="Gras"
        @click="format('bold')"
      >
        <IconBold size="xs" />
      </button>
      <button
        type="button"
        class="rounded p-1.5 text-sup-very-gray hover:bg-sup-withe"
        :class="{ 'bg-sup-withe text-sup-dark-green': isActive('italic') }"
        title="Italique"
        @click="format('italic')"
      >
        <IconItalic size="xs" />
      </button>
      <button
        type="button"
        class="rounded p-1.5 text-sup-very-gray hover:bg-sup-withe"
        :class="{ 'bg-sup-withe text-sup-dark-green': isActive('list') }"
        title="Liste"
        @click="format('list')"
      >
        <IconListBullet size="xs" />
      </button>
    </div>
    <EditorContent
      v-if="editor"
      :editor="editor"
      class="min-h-[110px] w-full rounded-md border border-sup-border bg-sup-withe p-3 text-[13.5px] text-sup-very-gray focus-within:border-sup-dark-green focus-within:ring-2 focus-within:ring-sup-light-green/30"
    />
  </div>
</template>

<style scoped>
/* Tailwind v4 processes each SFC <style> block in isolation, so @apply
   needs an explicit reference to the stylesheet that defines the utilities
   (and the sup-* tokens from tailwind.config.js) - see
   https://tailwindcss.com/docs/functions-and-directives#reference-directive */
@reference "../../assets/css/main.css";

:deep(.tiptap-content) {
  outline: none;
  min-height: 90px;
}

:deep(.tiptap-content p) {
  @apply my-1;
}

:deep(.tiptap-content h1),
:deep(.tiptap-content h2),
:deep(.tiptap-content h3) {
  @apply mt-2 mb-1 font-bold;
}

:deep(.tiptap-content strong) {
  @apply font-bold;
}

:deep(.tiptap-content em) {
  @apply italic;
}

:deep(.tiptap-content ul),
:deep(.tiptap-content ol) {
  @apply my-1 space-y-0.5 pl-5;
}

:deep(.tiptap-content ul) {
  list-style-type: disc;
}

:deep(.tiptap-content ol) {
  list-style-type: decimal;
}

:deep(.tiptap-content p.is-editor-empty:first-child::before) {
  @apply text-gray-400;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}
</style>
