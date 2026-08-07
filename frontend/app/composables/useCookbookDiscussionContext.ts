// composables/useCookbookDiscussionContext.ts

export interface CookbookDiscussionDefault {
  kind: "general" | "recipe" | "planning";
  id?: number;
}

export interface CookbookDiscussionContext {
  cookbookId: number;
  default: CookbookDiscussionDefault;
}

let guardRegistered = false;

// Layout-level state (see layouts/app.vue): which cookbook's discussion
// sidebar - and which of its channels to preselect - should be shown
// alongside the current page. Null outside any cookbook context.
//
// Reset to null on every navigation via a router guard (registered once,
// client-side only), *before* the destination page's own setup runs - a
// cookbook-context page then sets its own value during setup, so the
// layout only ever re-renders once with the final value. Without this
// reset, a page that doesn't set the context (e.g. the personal recipes
// list) would keep showing the previous page's cookbook sidebar.
export function useCookbookDiscussionContext() {
  const context = useState<CookbookDiscussionContext | null>(
    "cookbook-discussion-context",
    () => null,
  );

  if (import.meta.client && !guardRegistered) {
    guardRegistered = true;
    useRouter().beforeEach(() => {
      context.value = null;
    });
  }

  return context;
}
