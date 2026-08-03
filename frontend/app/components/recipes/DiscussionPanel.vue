<script setup lang="ts">
import { useApi } from "~/composables/useAPI";
import { relativeTime } from "~/composables/useRecipes";
import type { User } from "~/composables/useAuth";
import IconSend from "~/components/icons/IconSend.vue";

interface ChannelMessage {
  id: number;
  content: string;
  canal: string;
  author: User;
  cookbook: number;
  recipe: number | null;
  created_at: string;
}

interface PaginatedResponse<T> {
  results: T[];
}

const props = defineProps<{ cookbookId: number; recipeId: number }>();

const { get, post } = useApi();
const messages = ref<ChannelMessage[]>([]);
const newMessage = ref("");
const isLoading = ref(true);
const isSending = ref(false);

const load = async () => {
  isLoading.value = true;
  try {
    const response = await get<PaginatedResponse<ChannelMessage>>(
      `/cookbooks/${props.cookbookId}/recipes/${props.recipeId}/messages/`,
    );
    messages.value = response.results;
  } finally {
    isLoading.value = false;
  }
};

onMounted(load);

const send = async () => {
  const content = newMessage.value.trim();
  if (!content || isSending.value) return;
  isSending.value = true;
  try {
    const message = await post<ChannelMessage>(
      `/cookbooks/${props.cookbookId}/recipes/${props.recipeId}/messages/`,
      { content, canal: "recette" },
    );
    messages.value = [...messages.value, message];
    newMessage.value = "";
  } finally {
    isSending.value = false;
  }
};
</script>

<template>
  <div
    class="flex flex-col rounded-[14px] border border-sup-border bg-sup-withe p-[18px] shadow-sm"
  >
    <p class="mb-3 text-[14.5px] font-bold text-sup-very-gray">
      Discussion sur cette recette
    </p>

    <div v-if="isLoading" class="py-6 text-center text-[12px] text-gray-400">
      Chargement...
    </div>
    <div v-else class="mb-3 flex max-h-64 flex-col gap-3 overflow-y-auto">
      <p v-if="!messages.length" class="text-[12px] text-gray-400">
        Aucun message pour l'instant.
      </p>
      <div v-for="message in messages" :key="message.id" class="text-[13px]">
        <div class="flex items-baseline justify-between gap-2">
          <span class="font-semibold text-sup-very-gray">
            {{ message.author.first_name || message.author.username }}
          </span>
          <span class="text-[11px] text-gray-400">
            {{ relativeTime(message.created_at) }}
          </span>
        </div>
        <p class="text-sup-very-gray">{{ message.content }}</p>
      </div>
    </div>

    <div class="flex items-center gap-2">
      <input
        v-model="newMessage"
        type="text"
        placeholder="Écrire un message..."
        class="w-full rounded-md border border-sup-border bg-sup-withe px-3 py-[9px] text-[13.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30"
        @keyup.enter="send"
      />
      <button
        type="button"
        class="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-md bg-sup-dark-green text-sup-withe hover:brightness-105 disabled:opacity-40"
        :disabled="!newMessage.trim() || isSending"
        @click="send"
      >
        <IconSend size="xs" />
      </button>
    </div>
  </div>
</template>
