<script setup lang="ts">
import { capitalizeFirst } from "~/composables/useRecipes";
import IconChevron from "~/components/icons/IconChevron.vue";
import IconCheck from "~/components/icons/IconCheck.vue";
import IconClose from "~/components/icons/IconClose.vue";

// Picks from an existing catalogue (tags, ingredients...) instead of free
// typing - `fetchOptions` re-runs (debounced) against the search box, so the
// dropdown always reflects the real catalogue and its current filter text.
// The underlying model stays a single comma-separated string (matching what
// the recipe filters already send to the backend `tags`/`ingredients`
// params) - this component is just a friendlier way to build/edit it.
const props = withDefaults(
  defineProps<{
    label: string;
    searchPlaceholder?: string;
    emptyLabel?: string;
    fetchOptions: (
      search: string,
    ) => Promise<{ id: number; name: string; image?: string | null }[]>;
    // Tags are stored lowercase (see TagsPanel.vue) - display capitalized
    // here too for consistency. Ingredients aren't subject to that
    // convention, so this defaults to off.
    capitalizeLabels?: boolean;
  }>(),
  {
    searchPlaceholder: "Rechercher...",
    emptyLabel: "Aucun résultat.",
    capitalizeLabels: false,
  },
);

const modelValue = defineModel<string>({ required: true });

const open = ref(false);
const rootRef = ref<HTMLElement | null>(null);
const search = ref("");
const options = ref<{ id: number; name: string; image?: string | null }[]>(
  [],
);
// Accumulated (not replaced) across every search, keyed by lowercased name,
// so a chip for an already-selected item still shows its image even once
// it's scrolled out of the current search results.
const imagesByName = ref(new Map<string, string | null>());
let searchHandle: ReturnType<typeof setTimeout> | undefined;

const selected = computed<string[]>({
  get: () =>
    modelValue.value
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean),
  set: (names) => {
    modelValue.value = names.join(", ");
  },
});

const runSearch = () => {
  if (searchHandle) clearTimeout(searchHandle);
  searchHandle = setTimeout(async () => {
    const results = await props.fetchOptions(search.value);
    options.value = results;
    for (const option of results) {
      imagesByName.value.set(option.name.toLowerCase(), option.image ?? null);
    }
  }, 250);
};

const imageFor = (name: string) => imagesByName.value.get(name.toLowerCase());

// Load the current catalogue as soon as the dropdown opens, not just once
// the user starts typing - browsing without searching first should work.
watch(open, (isOpen) => {
  if (isOpen) runSearch();
});
watch(search, runSearch);

onClickOutside(rootRef, () => (open.value = false));

const display = (name: string) =>
  props.capitalizeLabels ? capitalizeFirst(name) : name;

const isSelected = (name: string) =>
  selected.value.some((s) => s.toLowerCase() === name.toLowerCase());

const toggleOption = (name: string) => {
  selected.value = isSelected(name)
    ? selected.value.filter((s) => s.toLowerCase() !== name.toLowerCase())
    : [...selected.value, name];
};

const removeSelected = (name: string) => {
  selected.value = selected.value.filter((s) => s !== name);
};
</script>

<template>
  <div ref="rootRef" class="relative">
    <label class="mb-1.5 block text-[12.5px] font-semibold text-sup-very-gray">
      {{ label }}
    </label>
    <button
      type="button"
      class="flex w-full items-center justify-between gap-2 rounded-md border border-sup-border bg-sup-withe px-3 py-[9px] text-left text-[13.5px] focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30"
      @click="open = !open"
    >
      <span
        class="truncate"
        :class="selected.length ? 'text-sup-very-gray' : 'text-gray-400'"
      >
        {{ selected.length ? selected.map(display).join(", ") : "Tous" }}
      </span>
      <IconChevron
        size="xs"
        :direction="open ? 'up' : 'down'"
        class="shrink-0 text-gray-400"
      />
    </button>

    <div
      v-if="open"
      class="absolute left-0 top-full z-10 mt-1 w-full min-w-[220px] rounded-md border border-sup-border bg-sup-withe p-2 shadow-lg"
    >
      <input
        v-model="search"
        type="text"
        :placeholder="searchPlaceholder"
        class="w-full rounded-md border border-sup-border bg-sup-withe px-3 py-[7px] text-[13px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30"
      />

      <ul class="mt-2 max-h-40 overflow-y-auto">
        <li v-for="option in options" :key="option.id">
          <button
            type="button"
            class="flex w-full items-center justify-between gap-2 rounded-md px-2 py-[7px] text-left text-[13px] text-sup-very-gray hover:bg-sup-light-gray"
            @click="toggleOption(option.name)"
          >
            <span class="flex min-w-0 items-center gap-2">
              <img
                v-if="option.image"
                :src="option.image"
                class="h-5 w-5 shrink-0 rounded object-cover"
              />
              <span class="truncate">{{ display(option.name) }}</span>
            </span>
            <IconCheck
              v-if="isSelected(option.name)"
              size="xs"
              class="shrink-0 text-sup-dark-green"
            />
          </button>
        </li>
        <li
          v-if="!options.length"
          class="px-2 py-[7px] text-[12px] text-gray-400"
        >
          {{ emptyLabel }}
        </li>
      </ul>
    </div>

    <div v-if="selected.length" class="mt-1.5 flex flex-wrap gap-1">
      <span
        v-for="name in selected"
        :key="name"
        class="inline-flex items-center gap-1 rounded-full bg-sup-light-green/15 py-0.5 pl-1 pr-2 text-[11px] font-medium text-sup-dark-green"
      >
        <img
          v-if="imageFor(name)"
          :src="imageFor(name)!"
          class="h-4 w-4 shrink-0 rounded-full object-cover"
        />
        {{ display(name) }}
        <button
          type="button"
          class="hover:text-sup-red-error"
          @click="removeSelected(name)"
        >
          <IconClose size="xs" />
        </button>
      </span>
    </div>
  </div>
</template>
