<script setup lang="ts">
import type { TagLine } from "~/composables/useRecipes";
import { uid, capitalizeFirst } from "~/composables/useRecipes";
import { useRecipeStore } from "~/stores/useRecipeStore";
import type { Tag } from "~/stores/useRecipeStore";
import IconTag from "~/components/icons/IconTag.vue";
import IconClose from "~/components/icons/IconClose.vue";
import IconPlus from "~/components/icons/IconPlus.vue";

const tags = defineModel<TagLine[]>({ required: true });
const store = useRecipeStore();

const TAG_TYPES = [
  { value: "repas", label: "Repas" },
  { value: "regime_alimentaire", label: "Régime alimentaire" },
];

const activeType = ref("repas");
const search = ref("");
const suggestions = ref<Tag[]>([]);
let searchHandle: ReturnType<typeof setTimeout> | undefined;

const isAlreadyAdded = (name: string) =>
  tags.value.some((t) => t.name.toLowerCase() === name.toLowerCase());

const runSearch = () => {
  if (searchHandle) clearTimeout(searchHandle);
  searchHandle = setTimeout(async () => {
    const results = await store.fetchTags(search.value || undefined);
    suggestions.value = results.filter((t) => t.type === activeType.value);
  }, 250);
};

watch([activeType, search], runSearch, { immediate: true });

const addExisting = (tag: Tag) => {
  if (isAlreadyAdded(tag.name)) return;
  tags.value = [
    ...tags.value,
    {
      key: uid("tag"),
      tagId: tag.id,
      // Lowercased even when copied from an existing (possibly legacy
      // mixed-case) Tag, so nothing re-submitted from here ever creates a
      // new case-variant row.
      name: tag.name.toLowerCase(),
      type: tag.type,
      description: tag.description ?? "",
    },
  ];
  search.value = "";
};

const addNew = () => {
  const name = search.value.trim().toLowerCase();
  if (!name || isAlreadyAdded(name)) return;
  tags.value = [
    ...tags.value,
    {
      key: uid("tag"),
      tagId: null,
      name,
      type: activeType.value,
      description: "",
    },
  ];
  search.value = "";
};

const removeTag = (key: string) => {
  tags.value = tags.value.filter((t) => t.key !== key);
};

const exactMatchExists = computed(() =>
  suggestions.value.some(
    (s) => s.name.toLowerCase() === search.value.trim().toLowerCase(),
  ),
);
</script>

<template>
  <div
    class="rounded-[14px] border border-sup-border bg-sup-withe p-[18px] shadow-sm"
  >
    <div
      class="mb-3 flex items-center gap-2 text-[14.5px] font-bold text-sup-very-gray"
    >
      <IconTag size="xs" />
      Tags
    </div>

    <div class="mb-3 flex flex-wrap gap-1.5">
      <span
        v-for="tag in tags"
        :key="tag.key"
        class="inline-flex items-center gap-1 rounded-full bg-sup-light-green/15 px-[10px] py-[3px] text-[11px] font-semibold text-sup-dark-green"
      >
        {{ capitalizeFirst(tag.name) }}
        <button
          type="button"
          class="hover:text-sup-red-error"
          @click="removeTag(tag.key)"
        >
          <IconClose size="xs" />
        </button>
      </span>
      <span v-if="!tags.length" class="text-[11px] text-gray-400">
        Aucun tag ajouté.
      </span>
    </div>

    <div class="mb-2 flex gap-1.5">
      <button
        v-for="t in TAG_TYPES"
        :key="t.value"
        type="button"
        class="rounded-md px-2 py-1 text-[11px] font-semibold transition"
        :class="
          activeType === t.value
            ? 'bg-sup-dark-green text-sup-withe'
            : 'bg-sup-light-gray text-sup-very-gray hover:bg-sup-border'
        "
        @click="activeType = t.value"
      >
        {{ t.label }}
      </button>
    </div>

    <input
      v-model="search"
      type="text"
      placeholder="Rechercher ou créer un tag..."
      class="w-full rounded-md border border-sup-border bg-sup-withe px-3 py-[9px] text-[13.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30"
      @keyup.enter="addNew"
    />

    <ul
      v-if="suggestions.length"
      class="mt-2 max-h-32 overflow-y-auto rounded-md border border-sup-border"
    >
      <li
        v-for="s in suggestions.filter((s) => !isAlreadyAdded(s.name))"
        :key="s.id"
      >
        <button
          type="button"
          class="flex w-full items-center justify-between px-3 py-2 text-left text-[13px] text-sup-very-gray hover:bg-sup-light-gray"
          @click="addExisting(s)"
        >
          {{ capitalizeFirst(s.name) }}
          <IconPlus size="xs" />
        </button>
      </li>
    </ul>

    <button
      v-if="search.trim() && !exactMatchExists"
      type="button"
      class="mt-2 flex items-center gap-1 text-[12px] font-semibold text-sup-dark-green hover:underline"
      @click="addNew"
    >
      <IconPlus size="xs" />
      Créer le tag « {{ capitalizeFirst(search.trim()) }} »
    </button>
  </div>
</template>
