<script setup lang="ts">
import type {
  Cookbook,
  CookbookRole,
} from "~/stores/cookbooks/useCookbookStore";
import { COOKBOOK_ROLE_LABELS } from "~/composables/useCookbooks";
import { relativeTime } from "~/composables/useRecipes";
import IconCookbook from "~/components/icons/IconCookbook.vue";

const props = defineProps<{
  cookbook: Cookbook;
  role: Exclude<CookbookRole, "admin">;
  to: string;
  // Overrides the displayed relative time - e.g. the cookbook's most recent
  // activity (a recipe/planning/member changing) rather than just the
  // cookbook's own `updated_at` (which only moves on a rename/icon change).
  activityAt?: string;
}>();

// Mirrors CookbookCard's placeholder gradients, used whenever the cookbook
// has no uploaded icon.
const placeholderGradients = [
  "bg-gradient-to-br from-[#FCEBB6] to-[#F1C40F]",
  "bg-gradient-to-br from-[#C7F0A4] to-[#84FA16]",
  "bg-gradient-to-br from-[#FBC7BB] to-[#E74C3C]",
  "bg-gradient-to-br from-[#AEE9C7] to-[#1A7F02]",
  "bg-gradient-to-br from-[#F7D9E3] to-[#E68FAE]",
  "bg-gradient-to-br from-[#BEE3F5] to-[#5EA8D6]",
  "bg-gradient-to-br from-[#EAFBDA] to-[#2AC204]",
];

const placeholderClass = computed(
  () => placeholderGradients[props.cookbook.id % placeholderGradients.length],
);

const roleBadgeClass = computed(() => {
  if (props.role === "editor" || props.role === "creator") {
    return "bg-sup-light-green/15 text-sup-dark-green";
  }
  return "border border-sup-border bg-sup-withe text-gray-400";
});
</script>

<template>
  <NuxtLink
    :to="to"
    class="flex items-center gap-3 rounded-[10px] border border-sup-border bg-sup-withe p-4 transition hover:-translate-y-px hover:shadow-md"
  >
    <div
      class="flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-md"
      :class="cookbook.icon ? 'bg-sup-light-gray' : placeholderClass"
    >
      <img
        v-if="cookbook.icon"
        :src="cookbook.icon"
        :alt="cookbook.name"
        class="h-full w-full object-cover"
      />
      <IconCookbook v-else size="sm" />
    </div>

    <div class="min-w-0 flex-1">
      <p class="truncate text-[13.5px] font-semibold text-sup-very-gray">
        {{ cookbook.name }}
      </p>
      <p class="truncate text-[11px] text-gray-400">
        par {{ cookbook.creator.first_name || cookbook.creator.username }} ·
        {{ relativeTime(activityAt || cookbook.updated_at) }}
      </p>
    </div>

    <span
      class="shrink-0 rounded-full px-[10px] py-[3px] text-[11px] font-semibold"
      :class="roleBadgeClass"
    >
      {{ COOKBOOK_ROLE_LABELS[role] }}
    </span>
  </NuxtLink>
</template>
