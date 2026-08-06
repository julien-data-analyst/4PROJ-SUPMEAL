<script setup lang="ts">
import { useApi } from "~/composables/useAPI";
import { relativeTime } from "~/composables/useRecipes";
import { useAuth } from "~/composables/useAuth";
import {
  useCookbookRoleFor,
  COOKBOOK_ROLE_RANK,
} from "~/composables/useCookbooks";
import type { User } from "~/composables/useAuth";
import IconSend from "~/components/icons/IconSend.vue";
import IconTrash from "~/components/icons/IconTrash.vue";

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

// Scoped to a specific recipe's channel when `recipeId` is given, otherwise
// the cookbook's global channel - used for a planning, which has no
// dedicated message channel of its own on the backend.
const props = defineProps<{
  cookbookId: number;
  recipeId?: number;
  title?: string;
}>();

const { get, post, del } = useApi();
const { user } = useAuth();
const cookbookRole = useCookbookRoleFor(() => props.cookbookId);

// Viewing and posting both require at least "commentator" - stricter than
// the backend (which lets a reader view, just not post) but matches what's
// wanted here: a reader shouldn't see the discussion at all.
const canComment = computed(
  () =>
    !!cookbookRole.value &&
    COOKBOOK_ROLE_RANK[cookbookRole.value] >= COOKBOOK_ROLE_RANK.commentator,
);
const isCookbookAdmin = computed(() => cookbookRole.value === "admin");

const endpoint = computed(() =>
  props.recipeId
    ? `/cookbooks/${props.cookbookId}/recipes/${props.recipeId}/messages/`
    : `/cookbooks/${props.cookbookId}/messages/`,
);

const messages = ref<ChannelMessage[]>([]);
const newMessage = ref("");
const isLoading = ref(true);
const isSending = ref(false);
const deletingId = ref<number | null>(null);

const load = async () => {
  if (!canComment.value) return;
  isLoading.value = true;
  try {
    const response = await get<PaginatedResponse<ChannelMessage>>(
      endpoint.value,
    );
    messages.value = response.results;
  } finally {
    isLoading.value = false;
  }
};

watch(canComment, load, { immediate: true });

const send = async () => {
  const content = newMessage.value.trim();
  if (!content || isSending.value) return;
  isSending.value = true;
  try {
    const message = await post<ChannelMessage>(endpoint.value, {
      content,
      canal: props.recipeId ? "recette" : "cookbook",
    });
    messages.value = [...messages.value, message];
    newMessage.value = "";
  } finally {
    isSending.value = false;
  }
};

const canDelete = (message: ChannelMessage) =>
  message.author.id === user.value?.id || isCookbookAdmin.value;

const remove = async (message: ChannelMessage) => {
  deletingId.value = message.id;
  try {
    await del(`${endpoint.value}${message.id}/`);
    messages.value = messages.value.filter((m) => m.id !== message.id);
  } finally {
    deletingId.value = null;
  }
};
</script>

<template>
  <div
    v-if="canComment"
    class="flex flex-col rounded-[14px] border border-sup-border bg-sup-withe p-[18px] shadow-sm"
  >
    <p class="mb-3 text-[14.5px] font-bold text-sup-very-gray">
      {{ title || "Discussion" }}
    </p>

    <div v-if="isLoading" class="py-6 text-center text-[12px] text-gray-400">
      Chargement...
    </div>
    <div v-else class="mb-3 flex max-h-64 flex-col gap-3 overflow-y-auto">
      <p v-if="!messages.length" class="text-[12px] text-gray-400">
        Aucun message pour l'instant.
      </p>
      <div
        v-for="message in messages"
        :key="message.id"
        class="group text-[13px]"
      >
        <div class="flex items-baseline justify-between gap-2">
          <span class="font-semibold text-sup-very-gray">
            {{ message.author.first_name || message.author.username }}
          </span>
          <span class="flex items-center gap-1.5 text-[11px] text-gray-400">
            {{ relativeTime(message.created_at) }}
            <button
              v-if="canDelete(message)"
              type="button"
              class="text-gray-400 opacity-0 hover:text-sup-red-error group-hover:opacity-100 disabled:opacity-50"
              title="Supprimer ce message"
              :disabled="deletingId === message.id"
              @click="remove(message)"
            >
              <IconTrash size="xs" />
            </button>
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
