import type { MarkdownStorage } from "tiptap-markdown";

// tiptap-markdown adds `editor.storage.markdown` at runtime but doesn't ship
// an augmentation for @tiptap/core's (deliberately empty, declaration-merge
// friendly) `Storage` interface - without this, `editor.storage.markdown` in
// StepEditor.vue fails typecheck with "Property 'markdown' does not exist".
declare module "@tiptap/core" {
  interface Storage {
    markdown: MarkdownStorage;
  }
}
