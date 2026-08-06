<script setup lang="ts">
import AppSidebar from "~/components/layout/AppSidebar.vue";
import ToastContainer from "~/components/common/ToastContainer.vue";
import CookbookDiscussionSidebar from "~/components/cookbook/CookbookDiscussionSidebar.vue";
import { useCookbookDiscussionContext } from "~/composables/useCookbookDiscussionContext";

// Set by whichever page is currently showing cookbook-scoped content (see
// the composable) - null everywhere else, so this sidebar only ever shows
// up while inside a shared cookbook (its own page, or one of its
// recipes/plannings). Kept here, in the layout, so it stays in the exact
// same spot across every page that sets it, instead of being re-built
// (and potentially drifting) per page.
const discussionContext = useCookbookDiscussionContext();
</script>

<template>
  <div
    class="flex min-h-screen bg-sup-light-gray text-[14px] text-sup-very-gray"
  >
    <AppSidebar />
    <div class="flex min-w-0 flex-1">
      <main class="min-w-0 flex-1 px-8 pb-[60px] pt-[26px]">
        <slot />
      </main>
      <aside
        v-if="discussionContext"
        class="sticky top-0 hidden h-screen w-[360px] shrink-0 flex-col border-l border-sup-border bg-sup-withe px-5 pb-[26px] pt-[26px] xl:flex"
      >
        <CookbookDiscussionSidebar
          :cookbook-id="discussionContext.cookbookId"
          :default-channel="discussionContext.default"
        />
      </aside>
    </div>
    <ToastContainer />
  </div>
</template>
