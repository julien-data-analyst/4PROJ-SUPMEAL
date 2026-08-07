<script setup lang="ts">
import IconChevron from "~/components/icons/IconChevron.vue";

const props = defineProps<{
  currentPage: number;
  totalPages: number;
}>();

const emit = defineEmits<{ "update:currentPage": [page: number] }>();

// Windowed page numbers (at most 5 buttons) centered on the current page.
const pageNumbers = computed(() => {
  const total = props.totalPages;
  const windowSize = Math.min(5, total);
  let start = Math.max(1, props.currentPage - Math.floor(windowSize / 2));
  const end = Math.min(total, start + windowSize - 1);
  start = Math.max(1, end - windowSize + 1);
  return Array.from({ length: end - start + 1 }, (_, i) => start + i);
});

const goToPage = (page: number) => {
  emit("update:currentPage", Math.min(Math.max(1, page), props.totalPages));
};
</script>

<template>
  <div v-if="totalPages > 1" class="flex items-center justify-center gap-1">
    <button
      type="button"
      class="flex h-8 w-8 items-center justify-center rounded-md text-gray-400 hover:bg-sup-light-gray hover:text-sup-very-gray disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent"
      :disabled="currentPage === 1"
      title="Page précédente"
      @click="goToPage(currentPage - 1)"
    >
      <IconChevron size="xs" direction="left" />
    </button>
    <button
      v-for="page in pageNumbers"
      :key="page"
      type="button"
      class="flex h-8 w-8 items-center justify-center rounded-md text-[12.5px] font-medium"
      :class="
        page === currentPage
          ? 'bg-sup-dark-green text-sup-withe'
          : 'text-sup-very-gray hover:bg-sup-light-gray'
      "
      @click="goToPage(page)"
    >
      {{ page }}
    </button>
    <button
      type="button"
      class="flex h-8 w-8 items-center justify-center rounded-md text-gray-400 hover:bg-sup-light-gray hover:text-sup-very-gray disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent"
      :disabled="currentPage === totalPages"
      title="Page suivante"
      @click="goToPage(currentPage + 1)"
    >
      <IconChevron size="xs" direction="right" />
    </button>
  </div>
</template>
